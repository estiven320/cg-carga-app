'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { formatEta } from '@/lib/format';
import type { ImportResult } from '@/types/tms';

interface ImportDialogProps {
  open: boolean;
  defaultSheet: string;
  onClose: () => void;
  onImported: (result: ImportResult) => void;
}

/**
 * Subida del Excel de despacho.
 *
 * La hoja es editable porque cambia de nombre cada dia
 * ("PROGRAMACION 3 DE SEPTIEMBRE" -> "... 4 DE SEPTIEMBRE"); el backend tolera
 * la coincidencia parcial, pero dejarlo explicito evita importar la hoja
 * equivocada de un libro con varias.
 */
export function ImportDialog({ open, defaultSheet, onClose, onImported }: ImportDialogProps) {
  const [file, setFile] = useState<File | null>(null);
  const [sheet, setSheet] = useState(defaultSheet);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);

  if (!open) return null;

  const submit = async () => {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const imported = await api.importDispatch(file, sheet);
      setResult(imported);
      onImported(imported);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Fallo la importacion');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-[2000] grid place-items-center bg-black/60 p-4"
      role="dialog"
      aria-modal="true"
      aria-label="Importar programacion"
    >
      <div className="card w-full max-w-lg p-6 shadow-overlay">
        <h2 className="text-base font-semibold text-content-primary">Importar programacion</h2>
        <p className="mt-1 text-xs text-content-secondary">
          Sube el archivo de despacho en formato .xlsx. Se leeran las columnas de documento, cliente,
          direccion, localidad, N/RUTA, peso, unidades, items y comentarios.
        </p>

        {!result ? (
          <>
            <label className="mt-5 block">
              <span className="text-xs font-medium text-content-secondary">Archivo</span>
              <input
                type="file"
                accept=".xlsx,.xls"
                className="input mt-1.5 file:mr-3 file:rounded file:border-0 file:bg-surface-overlay file:px-3 file:py-1 file:text-xs file:text-content-primary"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              />
            </label>

            <label className="mt-4 block">
              <span className="text-xs font-medium text-content-secondary">Hoja</span>
              <input className="input mt-1.5" value={sheet} onChange={(event) => setSheet(event.target.value)} />
            </label>

            {error && (
              <p className="mt-4 rounded-control border border-status-failed/30 bg-status-failed/10 px-3 py-2 text-xs text-status-failed">
                {error}
              </p>
            )}

            <div className="mt-6 flex justify-end gap-2">
              <button type="button" className="btn-ghost" onClick={onClose} disabled={busy}>
                Cancelar
              </button>
              <button type="button" className="btn-primary" onClick={submit} disabled={!file || busy}>
                {busy ? 'Procesando…' : 'Importar'}
              </button>
            </div>
          </>
        ) : (
          <ImportSummary result={result} onClose={onClose} />
        )}
      </div>
    </div>
  );
}

function ImportSummary({ result, onClose }: { result: ImportResult; onClose: () => void }) {
  return (
    <>
      <dl className="mt-5 grid grid-cols-4 gap-3 text-center">
        {[
          { label: 'Filas', value: result.totalRows },
          { label: 'Importadas', value: result.imported },
          { label: 'Omitidas', value: result.skipped },
          { label: 'Con error', value: result.failed },
        ].map((item) => (
          <div key={item.label} className="rounded-control bg-surface-sunken px-2 py-3">
            <dt className="text-[10px] uppercase tracking-wide text-content-muted">{item.label}</dt>
            <dd className="mt-1 text-lg font-semibold text-content-primary">{item.value}</dd>
          </div>
        ))}
      </dl>

      {result.pendingGeocode > 0 && (
        <p className="mt-4 rounded-control bg-brand-soft px-3 py-2.5 text-xs text-brand">
          Geocodificando {result.pendingGeocode} direcciones con Nominatim (1 por segundo para respetar
          la politica de uso de OpenStreetMap). Tiempo estimado:{' '}
          <strong>{formatEta(result.estimatedGeocodeMs)}</strong>. Los pines apareceran en el mapa a
          medida que se resuelvan.
        </p>
      )}

      {result.unmappedHeaders.length > 0 && (
        <p className="mt-3 text-[11px] text-content-muted">
          Columnas del archivo que no se usaron: {result.unmappedHeaders.slice(0, 8).join(', ')}
        </p>
      )}

      {result.issues.length > 0 && (
        <div className="mt-4 max-h-40 overflow-y-auto rounded-control border border-border-subtle">
          <ul className="divide-y divide-border-subtle text-[11px]">
            {result.issues.map((issue, index) => (
              <li key={`${issue.row}-${index}`} className="px-3 py-1.5 text-content-secondary">
                <span className="font-mono text-content-muted">Fila {issue.row}</span> · {issue.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-6 flex justify-end">
        <button type="button" className="btn-primary" onClick={onClose}>
          Ver en el mapa
        </button>
      </div>
    </>
  );
}
