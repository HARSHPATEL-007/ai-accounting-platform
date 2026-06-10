import 'package:equatable/equatable.dart';

enum DocumentType { invoice, bankStatement, receipt, contract, other }

enum SyncStatus { pending, synced, failed, processing }

class DocumentModel extends Equatable {
  final String id;
  final String clientId;
  final String fileName;
  final String filePath;
  final DocumentType type;
  final SyncStatus syncStatus;
  final DateTime createdAt;
  final String? ocrText;
  final Map<String, dynamic>? extractedData;
  final double? ocrConfidence;
  final String? errorMessage;

  const DocumentModel({
    required this.id,
    required this.clientId,
    required this.fileName,
    required this.filePath,
    required this.type,
    this.syncStatus = SyncStatus.pending,
    required this.createdAt,
    this.ocrText,
    this.extractedData,
    this.ocrConfidence,
    this.errorMessage,
  });

  DocumentModel copyWith({
    String? id,
    String? clientId,
    String? fileName,
    String? filePath,
    DocumentType? type,
    SyncStatus? syncStatus,
    DateTime? createdAt,
    String? ocrText,
    Map<String, dynamic>? extractedData,
    double? ocrConfidence,
    String? errorMessage,
  }) {
    return DocumentModel(
      id: id ?? this.id,
      clientId: clientId ?? this.clientId,
      fileName: fileName ?? this.fileName,
      filePath: filePath ?? this.filePath,
      type: type ?? this.type,
      syncStatus: syncStatus ?? this.syncStatus,
      createdAt: createdAt ?? this.createdAt,
      ocrText: ocrText ?? this.ocrText,
      extractedData: extractedData ?? this.extractedData,
      ocrConfidence: ocrConfidence ?? this.ocrConfidence,
      errorMessage: errorMessage ?? this.errorMessage,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'client_id': clientId,
    'file_name': fileName,
    'file_path': filePath,
    'type': type.name,
    'sync_status': syncStatus.name,
    'created_at': createdAt.toIso8601String(),
    'ocr_text': ocrText,
    'extracted_data': extractedData,
    'ocr_confidence': ocrConfidence,
    'error_message': errorMessage,
  };

  factory DocumentModel.fromJson(Map<String, dynamic> json) => DocumentModel(
    id: json['id'] as String,
    clientId: json['client_id'] as String,
    fileName: json['file_name'] as String,
    filePath: json['file_path'] as String,
    type: DocumentType.values.byName(json['type'] as String),
    syncStatus: SyncStatus.values.byName(json['sync_status'] as String),
    createdAt: DateTime.parse(json['created_at'] as String),
    ocrText: json['ocr_text'] as String?,
    extractedData: json['extracted_data'] as Map<String, dynamic>?,
    ocrConfidence: json['ocr_confidence'] as double?,
    errorMessage: json['error_message'] as String?,
  );

  @override
  List<Object?> get props => [id, clientId, fileName, syncStatus];
}
