import 'dart:io';
import 'package:dio/dio.dart';
import 'package:accounting_platform_mobile/models/document_model.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:logger/logger.dart';

class ApiService {
  final Dio _dio = Dio();
  final Logger _logger = Logger();
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();

  final String _baseUrl = 'https://api.accounting-platform.in';

  ApiService() {
    _dio.options.baseUrl = _baseUrl;
    _dio.options.connectTimeout = const Duration(seconds: 30);
    _dio.options.receiveTimeout = const Duration(seconds: 30);

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _secureStorage.read(key: 'auth_token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        options.headers['X-Client-Version'] = '1.0.0';
        options.headers['X-Platform'] = 'mobile';
        handler.next(options);
      },
      onError: (error, handler) {
        _logger.e('API Error: ${error.response?.statusCode} - ${error.message}');
        handler.next(error);
      },
    ));
  }

  Future<void> uploadDocument({
    required File file,
    required String clientId,
    required DocumentType documentType,
  }) async {
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(
        file.path,
        filename: file.path.split('/').last,
      ),
      'client_id': clientId,
      'document_type': documentType.name,
    });

    final response = await _dio.post(
      '/api/v1/ocr/process',
      data: formData,
      options: Options(
        headers: {'Content-Type': 'multipart/form-data'},
      ),
    );

    if (response.statusCode != 200) {
      throw Exception('Upload failed: ${response.statusMessage}');
    }

    _logger.i('Document uploaded successfully: ${response.data['document_id']}');
  }

  Future<Map<String, dynamic>> queryAI({
    required String query,
    required String clientId,
  }) async {
    final response = await _dio.post(
      '/api/v1/ai/query',
      data: {
        'query': query,
        'client_id': clientId,
        'user_id': await _secureStorage.read(key: 'user_id'),
      },
    );

    return response.data as Map<String, dynamic>;
  }

  Future<List<Map<String, dynamic>>> getComplianceItems(String clientId) async {
    final response = await _dio.get(
      '/api/v1/compliance/$clientId',
    );

    return List<Map<String, dynamic>>.from(response.data['items'] ?? []);
  }

  Future<Map<String, dynamic>> getDashboardMetrics(String clientId) async {
    final response = await _dio.get(
      '/api/v1/dashboard/$clientId/metrics',
    );

    return response.data as Map<String, dynamic>;
  }
}
