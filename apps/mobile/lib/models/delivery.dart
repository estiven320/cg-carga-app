class Delivery {
  Delivery({
    required this.id,
    required this.documentNumber,
    required this.clientName,
    required this.address,
    required this.status,
    this.locality,
    this.lat,
    this.lng,
    this.sequence,
    this.timeWindowStart,
    this.timeWindowEnd,
    this.requiresAppointment = false,
    this.comments,
    required this.weightKg,
    required this.units,
    required this.items,
  });

  final String id;
  final String documentNumber;
  final String clientName;
  final String address;
  final String? locality;
  final double? lat;
  final double? lng;
  final int? sequence;
  final String status;
  final String? timeWindowStart;
  final String? timeWindowEnd;
  final bool requiresAppointment;
  final String? comments;
  final double weightKg;
  final int units;
  final int items;

  bool get hasCoordinates => lat != null && lng != null;

  String? get timeWindowLabel {
    if (timeWindowStart == null && timeWindowEnd == null) return null;
    if (timeWindowStart == timeWindowEnd) return 'Cita $timeWindowStart';
    if (timeWindowStart != null && timeWindowEnd != null) {
      return '$timeWindowStart a $timeWindowEnd';
    }
    return timeWindowEnd != null ? 'Antes de $timeWindowEnd' : 'Desde $timeWindowStart';
  }

  factory Delivery.fromJson(Map<String, dynamic> json) => Delivery(
        id: json['id'] as String,
        documentNumber: json['documentNumber'] as String,
        clientName: json['clientNameRaw'] as String,
        address: json['address'] as String,
        locality: json['locality'] as String?,
        lat: (json['lat'] as num?)?.toDouble(),
        lng: (json['lng'] as num?)?.toDouble(),
        sequence: json['sequence'] as int?,
        status: json['status'] as String,
        timeWindowStart: json['timeWindowStart'] as String?,
        timeWindowEnd: json['timeWindowEnd'] as String?,
        requiresAppointment: json['requiresAppointment'] as bool? ?? false,
        comments: json['comments'] as String?,
        weightKg: (json['weightKg'] as num?)?.toDouble() ?? 0,
        units: json['units'] as int? ?? 0,
        items: json['items'] as int? ?? 0,
      );
}

class DriverRoute {
  DriverRoute({
    required this.id,
    required this.code,
    required this.color,
    required this.deliveries,
  });

  final String id;
  final String code;
  final String color;
  final List<Delivery> deliveries;

  int get delivered => deliveries.where((d) => d.status == 'DELIVERED').length;

  factory DriverRoute.fromJson(Map<String, dynamic> json) => DriverRoute(
        id: json['id'] as String,
        code: json['code'] as String,
        color: json['color'] as String? ?? '#2DD4BF',
        deliveries: (json['orders'] as List<dynamic>)
            .map((item) => Delivery.fromJson(item as Map<String, dynamic>))
            .toList(),
      );
}
