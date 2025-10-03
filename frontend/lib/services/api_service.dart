import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  //deployed API URL or localhost for development
  static const String baseUrl = 'http://localhost:8000/api/v1';
  


  static Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
      }),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Login failed: ${response.body}');
    }
  }

  static Future<Map<String, dynamic>> signup(
      String email, 
      String password, 
      String fullName, 
      String university
    ) async {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/signup'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email,
          'password': password,
          'full_name': fullName,
          'university': university,
        }),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Signup failed: ${response.body}');
      }
    }

    static Future<Map<String, dynamic>> getUserClasses({String? token}) async {
      final headers = {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      };
      final response = await http.get(
        Uri.parse('$baseUrl/classes'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to get classes: ${response.body}');
      }
    }

    static Future<Map<String, dynamic>> chatWithAI(
      String message, {
      String? conversationId,
      String? token,
      String? classContext,
    }) async {
      final headers = {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      };
      final body = {
        'message': message,
        if (conversationId != null) 'conversation_id': conversationId,
        if (classContext != null) 'class_context': classContext,
      };
      final response = await http.post(
        Uri.parse('$baseUrl/ai-study-buddy'),
        headers: headers,
        body: jsonEncode(body),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('AI chat failed: ${response.body}');
      }
    }
    

}