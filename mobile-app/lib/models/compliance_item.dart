import 'package:equatable/equatable.dart';

enum ComplianceStatus { completed, pending, overdue, inProgress }
enum ComplianceType { gst, tax, tds, audit, roc }

class ComplianceItem extends Equatable {
  final String id;
  final String title;
  final DateTime dueDate;
  final ComplianceStatus status;
  final ComplianceType type;
  final double progress;
  final String? description;

  const ComplianceItem({
    required this.id,
    required this.title,
    required this.dueDate,
    required this.status,
    required this.type,
    required this.progress,
    this.description,
  });

  bool get isOverdue => status != ComplianceStatus.completed && dueDate.isBefore(DateTime.now());
  int get daysRemaining => dueDate.difference(DateTime.now()).inDays;

  @override
  List<Object?> get props => [id, title, status, progress];
}
