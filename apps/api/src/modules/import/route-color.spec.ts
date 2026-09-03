import { colorForRoute, ROUTE_PALETTE } from './route-color';

describe('colorForRoute', () => {
  it('es determinista', () => {
    expect(colorForRoute('R-07')).toBe(colorForRoute('R-07'));
  });

  it('separa rutas consecutivas', () => {
    expect(colorForRoute('1')).not.toBe(colorForRoute('2'));
  });

  it('siempre devuelve un color de la paleta', () => {
    for (const code of ['1', 'R-12', 'ZONA NORTE', 'SIN RUTA', '']) {
      expect(ROUTE_PALETTE).toContain(colorForRoute(code) as any);
    }
  });
});
