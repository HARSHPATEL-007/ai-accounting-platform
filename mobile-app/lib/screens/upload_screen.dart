import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:uuid/uuid.dart';
import 'package:accounting_platform_mobile/models/document_model.dart';
import 'package:accounting_platform_mobile/services/ocr_service.dart';
import 'package:accounting_platform_mobile/services/sync_service.dart';
import 'package:permission_handler/permission_handler.dart';

class UploadScreen extends StatefulWidget {
  const UploadScreen({super.key});

  @override
  State<UploadScreen> createState() => _UploadScreenState();
}

class _UploadScreenState extends State<UploadScreen> {
  final ImagePicker _picker = ImagePicker();
  final OCRService _ocrService = OCRService();
  final SyncService _syncService = SyncService();
  final _uuid = const Uuid();

  bool _isProcessing = false;
  String _processingStatus = '';
  List<DocumentModel> _recentDocuments = [];

  @override
  void initState() {
    super.initState();
    _loadRecentDocuments();
  }

  Future<void> _loadRecentDocuments() async {
    final docs = await _syncService.getAllDocuments();
    setState(() => _recentDocuments = docs.take(10).toList());
  }

  Future<void> _captureImage(ImageSource source) async {
    if (source == ImageSource.camera) {
      final status = await Permission.camera.request();
      if (!status.isGranted) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Camera permission required')),
          );
        }
        return;
      }
    }

    final XFile? image = await _picker.pickImage(
      source: source,
      maxWidth: 2048,
      maxHeight: 2048,
      imageQuality: 85,
    );

    if (image == null) return;

    await _processDocument(image);
  }

  Future<void> _processDocument(XFile image) async {
    setState(() {
      _isProcessing = true;
      _processingStatus = 'Running OCR...';
    });

    try {
      final appDir = await getApplicationDocumentsDirectory();
      final fileName = '${_uuid.v4()}_${image.name}';
      final savedPath = '${appDir.path}/documents/$fileName';
      await Directory('${appDir.path}/documents').create(recursive: true);
      await File(image.path).copy(savedPath);

      setState(() => _processingStatus = 'Extracting text...');
      final ocrText = await _ocrService.recognizeText(File(savedPath));

      setState(() => _processingStatus = 'Analyzing document...');
      final extractedData = await _ocrService.extractStructuredData(ocrText);

      final document = DocumentModel(
        id: _uuid.v4(),
        clientId: '22222222-2222-2222-2222-222222222222',
        fileName: image.name,
        filePath: savedPath,
        type: DocumentType.invoice,
        createdAt: DateTime.now(),
        ocrText: ocrText,
        extractedData: extractedData,
        ocrConfidence: 0.85,
      );

      await _syncService.queueDocumentForUpload(document);

      setState(() {
        _isProcessing = false;
        _processingStatus = 'Document uploaded successfully!';
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Document uploaded. Processing...'),
            backgroundColor: Colors.green,
          ),
        );
      }

      await _loadRecentDocuments();
    } catch (e) {
      setState(() {
        _isProcessing = false;
        _processingStatus = 'Error: $e';
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to process document: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                children: [
                  const Icon(Icons.cloud_upload, size: 48, color: Colors.blue),
                  const SizedBox(height: 8),
                  const Text(
                    'Upload Invoice or Receipt',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Take a photo or select from gallery',
                    style: TextStyle(color: Colors.grey[600]),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: _isProcessing ? null : () => _captureImage(ImageSource.camera),
                          icon: const Icon(Icons.camera_alt),
                          label: const Text('Camera'),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: _isProcessing ? null : () => _captureImage(ImageSource.gallery),
                          icon: const Icon(Icons.photo_library),
                          label: const Text('Gallery'),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          if (_isProcessing) ...[
            const SizedBox(height: 16),
            const LinearProgressIndicator(),
            const SizedBox(height: 8),
            Text(
              _processingStatus,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.blue),
            ),
          ],

          const SizedBox(height: 24),
          const Text(
            'Recent Documents',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: _recentDocuments.isEmpty
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.folder_open, size: 64, color: Colors.grey[400]),
                        const SizedBox(height: 8),
                        Text(
                          'No documents yet',
                          style: TextStyle(color: Colors.grey[600]),
                        ),
                      ],
                    ),
                  )
                : ListView.builder(
                    itemCount: _recentDocuments.length,
                    itemBuilder: (context, index) {
                      final doc = _recentDocuments[index];
                      return ListTile(
                        leading: Icon(
                          doc.type == DocumentType.invoice
                              ? Icons.receipt
                              : doc.type == DocumentType.bankStatement
                                  ? Icons.account_balance
                                  : Icons.description,
                          color: doc.syncStatus == SyncStatus.synced
                              ? Colors.green
                              : doc.syncStatus == SyncStatus.pending
                                  ? Colors.orange
                                  : Colors.red,
                        ),
                        title: Text(doc.fileName),
                        subtitle: Text(
                          '${doc.createdAt.toLocal()} - ${doc.syncStatus.name}',
                        ),
                        trailing: doc.syncStatus == SyncStatus.synced
                            ? const Icon(Icons.check_circle, color: Colors.green)
                            : doc.syncStatus == SyncStatus.pending
                                ? const Icon(Icons.sync, color: Colors.orange)
                                : const Icon(Icons.error, color: Colors.red),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _ocrService.dispose();
    super.dispose();
  }
}
