import { BadRequestException, Injectable, Logger } from '@nestjs/common';
import { Workbook, type Row, type Worksheet } from 'exceljs';
import { COLUMN_SPECS, mapColumns, normalizeHeader, type OrderColumn } from './column-mapping';
import { parseTimeWindow, type TimeWindow } from './time-window.parser';

export interface ParsedOrderRow {
  rowNumber: number;
  documentNumber: string;
  clientName: string;
  address: string;
  locality: string | null;
  routeCode: string;
  weightKg: number;
  units: number;
  items: number;
  comments: string | null;
  timeWindow: TimeWindow;
}

export interface ParseIssue {
  row: number;
  column?: string;
  message: string;
}

export interface ParseResult {
  sheetName: string;
  dispatchDate: Date;
  headerRowNumber: number;
  mapping: Partial<Record<OrderColumn, number>>;
  unmappedHeaders: string[];
  rows: ParsedOrderRow[];
  issues: ParseIssue[];
  totalRows: number;
  skippedRows: number;
}

const MONTHS_ES: Record<string, number> = {
  ENERO: 0, FEBRERO: 1, MARZO: 2, ABRIL: 3, MAYO: 4, JUNIO: 5,
  JULIO: 6, AGOSTO: 7, SEPTIEMBRE: 8, SETIEMBRE: 8, OCTUBRE: 9,
  NOVIEMBRE: 10, DICIEMBRE: 11,
};

@Injectable()
export class ExcelParserService {
  private readonly logger = new Logger(ExcelParserService.name);

  /**
   * Lee el archivo de despacho y devuelve filas tipadas.
   *
   * @param buffer  contenido del .xlsx subido por el administrador
   * @param sheetName hoja objetivo (por defecto "PROGRAMACION 3 DE SEPTIEMBRE")
   */
  async parse(buffer: Buffer, sheetName: string, dispatchDateOverride?: Date): Promise<ParseResult> {
    const workbook = new Workbook();
    await workbook.xlsx.load(buffer as unknown as ArrayBuffer);

    const sheet = this.findSheet(workbook, sheetName);
    const { headerRowNumber, mapping, unmapped } = this.locateHeader(sheet);

    const issues: ParseIssue[] = [];
    const rows: ParsedOrderRow[] = [];
    let skipped = 0;
    let total = 0;

    sheet.eachRow({ includeEmpty: false }, (row, rowNumber) => {
      if (rowNumber <= headerRowNumber) return;
      total += 1;

      const documentNumber = this.readString(row, mapping.documentNumber);
      const address = this.readString(row, mapping.address);
      const routeCode = this.readString(row, mapping.routeCode);
      const clientName = this.readString(row, mapping.clientName);

      // Filas de subtotales / separadores: sin documento y sin direccion.
      if (!documentNumber && !address && !clientName) {
        skipped += 1;
        return;
      }

      if (!documentNumber) {
        issues.push({ row: rowNumber, column: 'Número de documento', message: 'Fila sin numero de documento' });
        skipped += 1;
        return;
      }
      if (!address) {
        issues.push({ row: rowNumber, column: 'Direccion', message: `Documento ${documentNumber} sin direccion: no se podra geocodificar` });
      }
      if (!routeCode) {
        issues.push({ row: rowNumber, column: 'N/RUTA', message: `Documento ${documentNumber} sin N/RUTA: se asigna a "SIN RUTA"` });
      }

      const comments = this.readString(row, mapping.comments) || null;

      rows.push({
        rowNumber,
        documentNumber,
        clientName: clientName || 'SIN NOMBRE',
        address,
        locality: this.readString(row, mapping.locality) || null,
        routeCode: routeCode || 'SIN RUTA',
        weightKg: this.readNumber(row, mapping.weightKg),
        units: Math.round(this.readNumber(row, mapping.units)),
        items: Math.round(this.readNumber(row, mapping.items)),
        comments,
        timeWindow: parseTimeWindow(comments),
      });
    });

    return {
      sheetName: sheet.name,
      dispatchDate: dispatchDateOverride ?? this.inferDispatchDate(sheet.name),
      headerRowNumber,
      mapping,
      unmappedHeaders: unmapped,
      rows,
      issues,
      totalRows: total,
      skippedRows: skipped,
    };
  }

  /** Lista las hojas disponibles: la UI la usa cuando el nombre no coincide. */
  async listSheets(buffer: Buffer): Promise<string[]> {
    const workbook = new Workbook();
    await workbook.xlsx.load(buffer as unknown as ArrayBuffer);
    return workbook.worksheets.map((sheet) => sheet.name);
  }

  // ---------------------------------------------------------------- helpers

  private findSheet(workbook: Workbook, sheetName: string): Worksheet {
    const target = normalizeHeader(sheetName);

    const exact = workbook.worksheets.find((sheet) => normalizeHeader(sheet.name) === target);
    if (exact) return exact;

    // Tolerancia: la hoja cambia de nombre cada dia ("PROGRAMACION 4 DE
    // SEPTIEMBRE"), asi que tambien se acepta coincidencia parcial.
    const partial = workbook.worksheets.find(
      (sheet) =>
        normalizeHeader(sheet.name).includes(target) || target.includes(normalizeHeader(sheet.name)),
    );
    if (partial) {
      this.logger.warn(`Hoja "${sheetName}" no existe; se usa la coincidencia parcial "${partial.name}"`);
      return partial;
    }

    throw new BadRequestException(
      `No se encontro la hoja "${sheetName}". Hojas disponibles: ${workbook.worksheets
        .map((sheet) => sheet.name)
        .join(', ')}`,
    );
  }

  /**
   * El encabezado rara vez esta en la fila 1: los archivos traen titulo, logo
   * y filas en blanco. Se escanean las primeras 25 filas y se elige la que
   * mapee mas columnas conocidas.
   */
  private locateHeader(sheet: Worksheet) {
    let best: { rowNumber: number; score: number; mapping: any; unmapped: string[] } | null = null;

    const limit = Math.min(sheet.rowCount || 25, 25);
    for (let rowNumber = 1; rowNumber <= limit; rowNumber += 1) {
      const values = sheet.getRow(rowNumber).values as unknown[];
      // ExcelJS entrega `values` 1-based con un hueco en el indice 0.
      const cells = Array.isArray(values) ? values.slice(1) : [];
      if (cells.length === 0) continue;

      const { mapping, unmapped } = mapColumns(cells);
      const score = Object.keys(mapping).length;
      if (!best || score > best.score) best = { rowNumber, score, mapping, unmapped };
    }

    if (!best || best.score === 0) {
      throw new BadRequestException(
        `No se pudo identificar la fila de encabezados en la hoja "${sheet.name}".`,
      );
    }

    const missing = COLUMN_SPECS.filter(
      (spec) => spec.required && best!.mapping[spec.key] === undefined,
    ).map((spec) => spec.canonical);

    if (missing.length > 0) {
      throw new BadRequestException(
        `Faltan columnas obligatorias en "${sheet.name}": ${missing.join(', ')}. ` +
          `Encabezados detectados en la fila ${best.rowNumber}.`,
      );
    }

    return { headerRowNumber: best.rowNumber, mapping: best.mapping, unmapped: best.unmapped };
  }

  private readString(row: Row, column?: number): string {
    if (!column) return '';
    const cell = row.getCell(column);
    const value = cell?.value;
    if (value === null || value === undefined) return '';

    if (typeof value === 'object') {
      // Celdas con formula, hipervinculo o rich text.
      const anyValue = value as any;
      if ('result' in anyValue) return String(anyValue.result ?? '').trim();
      if ('text' in anyValue) return String(anyValue.text ?? '').trim();
      if ('richText' in anyValue) {
        return anyValue.richText.map((part: any) => part.text).join('').trim();
      }
      if (value instanceof Date) return value.toISOString();
    }
    return String(value).replace(/\s+/g, ' ').trim();
  }

  private readNumber(row: Row, column?: number): number {
    const raw = this.readString(row, column);
    if (!raw) return 0;

    // Normaliza formato colombiano: "1.234,50" -> 1234.50
    const cleaned = raw
      .replace(/[^\d,.-]/g, '')
      .replace(/\.(?=\d{3}(\D|$))/g, '')
      .replace(',', '.');

    const parsed = Number.parseFloat(cleaned);
    return Number.isFinite(parsed) ? parsed : 0;
  }

  /** "PROGRAMACION 3 DE SEPTIEMBRE" -> 2026-09-03 (ano en curso). */
  private inferDispatchDate(sheetName: string): Date {
    const normalized = normalizeHeader(sheetName);
    const match = normalized.match(/(\d{1,2})\s*DE\s*([A-Z]+)(?:\s*(?:DE\s*)?(\d{4}))?/);

    if (match) {
      const day = Number.parseInt(match[1], 10);
      const month = MONTHS_ES[match[2]];
      const year = match[3] ? Number.parseInt(match[3], 10) : new Date().getFullYear();
      if (month !== undefined && day >= 1 && day <= 31) {
        return new Date(Date.UTC(year, month, day));
      }
    }

    this.logger.warn(`No se pudo inferir la fecha desde "${sheetName}"; se usa la fecha de hoy.`);
    const today = new Date();
    return new Date(Date.UTC(today.getFullYear(), today.getMonth(), today.getDate()));
  }
}
