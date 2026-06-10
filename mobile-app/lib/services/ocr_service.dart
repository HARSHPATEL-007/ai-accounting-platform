import 'dart:io';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import 'package:logger/logger.dart';

class OCRService {
  final TextRecognizer _textRecognizer = TextRecognizer(script: TextRecognitionScript.latin);
  final Logger _logger = Logger();

  Future<String> recognizeText(File imageFile) async {
    try {
      final inputImage = InputImage.fromFile(imageFile);
      final recognizedText = await _textRecognizer.processImage(inputImage);

      _logger.i('OCR completed: ${recognizedText.text.length} characters');
      return recognizedText.text;
    } catch (e) {
      _logger.e('OCR failed: $e');
      throw Exception('OCR processing failed: $e');
    }
  }

  Future<Map<String, dynamic>> extractStructuredData(String rawText) async {
    final data = <String, dynamic>{};

    // Extract GSTIN (Indian GST Number)
    final gstinRegex = RegExp(r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b');
    final gstinMatches = gstinRegex.allMatches(rawText);
    if (gstinMatches.isNotEmpty) {
      data['gstin'] = gstinMatches.first.group(0);
    }

    // Extract amounts (INR format)
    final amountRegex = RegExp(r'(?:Rs\.?|INR|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)');
    final amountMatches = amountRegex.allMatches(rawText);
    data['amounts'] = amountMatches.map((m) => m.group(1)).toList();

    // Extract dates
    final dateRegex = RegExp(r'\b\d{2}[/-]\d{2}[/-]\d{4}\b');
    final dateMatches = dateRegex.allMatches(rawText);
    data['dates'] = dateMatches.map((m) => m.group(0)).toList();

    // Extract invoice numbers
    final invoiceRegex = RegExp(r'(?:Invoice|Inv|Bill)\s*(?:No|Number|#)?[:\s]*([A-Z0-9/-]+)', caseSensitive: false);
    final invoiceMatch = invoiceRegex.firstMatch(rawText);
    if (invoiceMatch != null) {
      data['invoice_number'] = invoiceMatch.group(1);
    }

    // Extract HSN codes
    final hsnRegex = RegExp(r'\b[0-9]{4,8}\b');
    final hsnMatches = hsnRegex.allMatches(rawText);
    data['hsn_codes'] = hsnMatches.map((m) => m.group(0)).toList();

    return data;
  }

  void dispose() {
    _textRecognizer.close();
  }
}
