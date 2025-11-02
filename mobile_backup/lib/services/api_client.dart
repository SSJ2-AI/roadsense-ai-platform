import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../models/detection.dart';

class ApiClient {
  static String get baseUrl => 'https://roadsense-api-987284702676.us-central1.run.app';
  static String get apiKey => const String.fromEnvironment('API_KEY');

  static Future<Detection> uploadDetection(
    File file, {
    String? deviceId,
    double? lat,
    double? lng,
    double? alt,
  }) async {
    final uri = Uri.parse('$baseUrl/v1/detections');
    final req = http.MultipartRequest('POST', uri);
    req.headers['x-api-key'] = apiKey;
    req.files.add(await http.MultipartFile.fromPath('image', file.path));
    if (deviceId != null) req.fields['deviceId'] = deviceId;
    if (lat != null) req.fields['lat'] = lat.toString();
    if (lng != null) req.fields['lng'] = lng.toString();
    if (alt != null) req.fields['alt'] = alt.toString();

    final resp = await http.Response.fromStream(await req.send());
    if (resp.statusCode >= 200 && resp.statusCode < 300) {
      return Detection.fromJson(jsonDecode(resp.body));
    }
    throw Exception('Upload failed: ${resp.statusCode} ${resp.body}');
  }
}
