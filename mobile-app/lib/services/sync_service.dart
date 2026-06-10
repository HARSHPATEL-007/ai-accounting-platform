import 'dart:async';
import 'dart:io';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'package:path_provider/path_provider.dart';
import 'package:accounting_platform_mobile/models/document_model.dart';
import 'package:accounting_platform_mobile/services/api_service.dart';
import 'package:logger/logger.dart';

class SyncService {
  static final SyncService _instance = SyncService._internal();
  factory SyncService() => _instance;
  SyncService._internal();

  final Logger _logger = Logger();
  Database? _database;
  final ApiService _apiService = ApiService();
  final StreamController<SyncStatus> _syncController = StreamController<SyncStatus>.broadcast();
  Stream<SyncStatus> get syncStream => _syncController.stream;

  Future<void> initialize() async {
    await _initDatabase();
    _startConnectivityListener();
  }

  Future<void> _initDatabase() async {
    final documentsDirectory = await getApplicationDocumentsDirectory();
    final path = join(documentsDirectory.path, 'accounting_platform.db');

    _database = await openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE documents (
            id TEXT PRIMARY KEY,
            client_id TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            type TEXT NOT NULL,
            sync_status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            ocr_text TEXT,
            extracted_data TEXT,
            ocr_confidence REAL,
            error_message TEXT
          )
        ''');

        await db.execute('''
          CREATE TABLE compliance_items (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT NOT NULL,
            type TEXT NOT NULL,
            progress REAL NOT NULL,
            description TEXT
          )
        ''');

        await db.execute('''
          CREATE TABLE pending_uploads (
            id TEXT PRIMARY KEY,
            file_path TEXT NOT NULL,
            client_id TEXT NOT NULL,
            document_type TEXT NOT NULL,
            retry_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
          )
        ''');
      },
    );
    _logger.i('Database initialized at $path');
  }

  void _startConnectivityListener() {
    Connectivity().onConnectivityChanged.listen((result) {
      if (result != ConnectivityResult.none) {
        _logger.i('Connectivity restored, starting sync...');
        _syncPendingDocuments();
      }
    });
  }

  Future<void> _syncPendingDocuments() async {
    if (_database == null) return;

    final pendingDocs = await _database!.query(
      'documents',
      where: 'sync_status = ?',
      whereArgs: ['pending'],
    );

    for (final doc in pendingDocs) {
      try {
        final document = DocumentModel.fromJson(doc);
        await _uploadDocument(document);
      } catch (e) {
        _logger.e('Sync failed for document ${doc['id']}: $e');
      }
    }
  }

  Future<void> _uploadDocument(DocumentModel document) async {
    _syncController.add(SyncStatus.processing);

    try {
      final file = File(document.filePath);
      if (!file.existsSync()) {
        throw Exception('File not found: ${document.filePath}');
      }

      await _apiService.uploadDocument(
        file: file,
        clientId: document.clientId,
        documentType: document.type,
      );

      await _database!.update(
        'documents',
        {'sync_status': 'synced'},
        where: 'id = ?',
        whereArgs: [document.id],
      );

      _syncController.add(SyncStatus.synced);
      _logger.i('Document ${document.id} synced successfully');
    } catch (e) {
      await _database!.update(
        'documents',
        {
          'sync_status': 'failed',
          'error_message': e.toString(),
        },
        where: 'id = ?',
        whereArgs: [document.id],
      );
      _syncController.add(SyncStatus.failed);
      _logger.e('Failed to sync document ${document.id}: $e');
    }
  }

  Future<void> queueDocumentForUpload(DocumentModel document) async {
    if (_database == null) return;

    await _database!.insert('documents', document.toJson());

    final connectivity = await Connectivity().checkConnectivity();
    if (connectivity != ConnectivityResult.none) {
      await _uploadDocument(document);
    } else {
      _logger.i('Document ${document.id} queued for upload (offline)');
    }
  }

  Future<List<DocumentModel>> getPendingDocuments() async {
    if (_database == null) return [];

    final docs = await _database!.query(
      'documents',
      where: 'sync_status = ?',
      whereArgs: ['pending'],
      orderBy: 'created_at DESC',
    );

    return docs.map((d) => DocumentModel.fromJson(d)).toList();
  }

  Future<List<DocumentModel>> getAllDocuments() async {
    if (_database == null) return [];

    final docs = await _database!.query(
      'documents',
      orderBy: 'created_at DESC',
    );

    return docs.map((d) => DocumentModel.fromJson(d)).toList();
  }

  Future<void> close() async {
    await _database?.close();
    await _syncController.close();
  }
}
