import { normalizeAddress, scoreResult } from './address-normalizer';

describe('normalizeAddress', () => {
  it('expande abreviaturas viales y agrega Colombia', () => {
    const result = normalizeAddress('Cra 68 # 24-35', 'Bogotá');
    expect(result.query).toBe('CARRERA 68 24-35, BOGOTA, COLOMBIA');
  });

  it('produce el mismo hash para variantes de la misma direccion', () => {
    const a = normalizeAddress('CL 100 No 8-20', 'BOGOTA');
    const b = normalizeAddress('Calle 100 # 8 - 20', 'Bogotá');
    expect(a.hash).toBe(b.hash);
  });

  it('elimina el ruido que Nominatim no resuelve', () => {
    const result = normalizeAddress('Av 68 # 5-30 Bodega 12 Interior 3', 'Bogota');
    expect(result.query).not.toMatch(/BODEGA|INTERIOR/);
    expect(result.query).toContain('AVENIDA 68');
  });

  it('funciona sin localidad', () => {
    expect(normalizeAddress('Diagonal 45 12-30').query).toBe('DIAGONAL 45 12-30, COLOMBIA');
  });
});

describe('scoreResult', () => {
  it('premia los resultados a nivel de direccion', () => {
    expect(scoreResult(30, 0.4)).toBeGreaterThan(scoreResult(14, 0.4));
  });

  it('penaliza los aciertos que solo llegan al municipio', () => {
    expect(scoreResult(12, 0.3, 'place')).toBeLessThan(0.35);
  });
});
