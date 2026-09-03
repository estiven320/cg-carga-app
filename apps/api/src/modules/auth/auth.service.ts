import { Injectable, UnauthorizedException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { compare, hash } from 'bcryptjs';
import { PrismaService } from '../../prisma/prisma.service';

@Injectable()
export class AuthService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly jwt: JwtService,
  ) {}

  async login(email: string, password: string) {
    const user = await this.prisma.user.findUnique({ where: { email: email.toLowerCase() } });
    if (!user || !user.active || !(await compare(password, user.passwordHash))) {
      // Mensaje unico para no revelar si el correo existe.
      throw new UnauthorizedException('Credenciales invalidas');
    }

    return {
      accessToken: await this.jwt.signAsync({ sub: user.id, email: user.email, role: user.role }),
      user: { id: user.id, email: user.email, fullName: user.fullName, role: user.role },
    };
  }

  /** Login de la app movil: documento + clave del conductor. */
  async loginDriver(documentNumber: string, phone: string) {
    const driver = await this.prisma.driver.findUnique({ where: { documentNumber } });
    const digits = phone.replace(/\D/g, '');
    if (!driver || !driver.active || !driver.phone.endsWith(digits.slice(-10))) {
      throw new UnauthorizedException('Credenciales invalidas');
    }

    return {
      accessToken: await this.jwt.signAsync({ sub: driver.id, role: 'DRIVER', type: 'driver' }),
      driver: { id: driver.id, fullName: driver.fullName, vehiclePlate: driver.vehiclePlate },
    };
  }

  static hashPassword(plain: string): Promise<string> {
    return hash(plain, 10);
  }
}
