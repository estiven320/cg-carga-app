import { parseTimeWindow } from './time-window.parser';

describe('parseTimeWindow', () => {
  it('lee un rango explicito con minutos', () => {
    expect(parseTimeWindow('ENTREGAR DE 8:00 A 12:00')).toMatchObject({
      start: '08:00',
      end: '12:00',
    });
  });

  it('interpreta el meridiano', () => {
    expect(parseTimeWindow('RECIBEN DE 7 AM A 3 PM')).toMatchObject({
      start: '07:00',
      end: '15:00',
    });
  });

  it('asume tarde para horas ambiguas de 1 a 6', () => {
    expect(parseTimeWindow('HORARIO 8 A 4')).toMatchObject({ start: '08:00', end: '16:00' });
  });

  it('reconoce limite superior', () => {
    expect(parseTimeWindow('SOLO ANTES DE LAS 11')).toMatchObject({ start: null, end: '11:00' });
  });

  it('reconoce limite inferior', () => {
    expect(parseTimeWindow('DESPUES DE LA 1 PM')).toMatchObject({ start: '13:00', end: null });
  });

  it('marca las entregas con cita', () => {
    expect(parseTimeWindow('CITA 10:30')).toMatchObject({
      start: '10:30',
      end: '10:30',
      requiresAppointment: true,
    });
  });

  it('combina rango y cita', () => {
    expect(parseTimeWindow('HORARIO 6AM-2PM / AGENDAR CITA')).toMatchObject({
      start: '06:00',
      end: '14:00',
      requiresAppointment: true,
    });
  });

  it('devuelve nulos cuando no hay horario', () => {
    expect(parseTimeWindow('LLAMAR AL LLEGAR')).toEqual({
      start: null,
      end: null,
      requiresAppointment: false,
    });
    expect(parseTimeWindow(null)).toEqual({ start: null, end: null, requiresAppointment: false });
  });
});
