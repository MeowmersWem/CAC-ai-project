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

  static Future<Map<String, dynamic>> getUserClasses() async {
    final response = await http.get(
      Uri.parse('$baseUrl/classes'),
      headers: {'Content-Type': 'application/json'},
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to get classes: ${response.body}');
    }
  }

  static Future<Map<String, dynamic>> chatWithAI(String message) async {
    final response = await http.post(
      Uri.parse('$baseUrl/ai-study-buddy'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'message': message,
      }),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('AI chat failed: ${response.body}');
    }
  }
}