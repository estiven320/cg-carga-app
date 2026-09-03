/** Token de inyeccion en archivo propio para evitar un ciclo de imports
 *  entre `notifications.module.ts` y `notifications.service.ts`. */
export const WHATSAPP_PROVIDER = Symbol('WHATSAPP_PROVIDER');
