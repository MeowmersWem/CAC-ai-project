import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  // Deployed API URL or localhost for development
  // If testing on Android emulator, use: http://10.0.2.2:8000/api/v1
  static const String baseUrl = 'http://localhost:8080/api/v1';
  


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

  static Future<void> signOut({String? token}) async {
    final headers = {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
    final response = await http.post(
      Uri.parse('$baseUrl/auth/signout'),
      headers: headers,
    );
    if (response.statusCode != 200) {
      throw Exception('Sign out failed: ${response.body}');
    }
  }
  static Future<Map<String, dynamic>> joinClass({
    required String classCode,
    String? email,
    String? token,
  }) async {
    final headers = {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
    final uri = Uri.parse('$baseUrl/classes/join').replace(queryParameters: {
      if (email != null) 'email': email,
    });
    final response = await http.post(
      uri,
      headers: headers,
      body: jsonEncode({ 'class_code': classCode }),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Join class failed: ${response.body}');
    }
  }
  static Future<Map<String, dynamic>> createClass({
    required String name,
    String? email,
    String? token,
  }) async {
    final headers = {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
    final uri = Uri.parse('$baseUrl/classes').replace(queryParameters: {
      if (email != null) 'email': email,
    });
    final response = await http.post(
      uri,
      headers: headers,
      body: jsonEncode({ 'name': name }),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Create class failed: ${response.body}');
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

  static Future<Map<String, dynamic>> getProfile({String? token, String? email}) async {
    final headers = {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
    final uri = Uri.parse('$baseUrl/users/me').replace(queryParameters: {
      if (email != null) 'email': email,
    });
    final response = await http.get(
      uri,
      headers: headers,
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Get profile failed: ${response.body}');
    }
  }

  static Future<Map<String, dynamic>> getClassRoster({
    required String classId,
    String? token,
  }) async {
    final headers = {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
    final response = await http.get(
      Uri.parse('$baseUrl/classes/$classId/roster'),
      headers: headers,
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Get roster failed: ${response.body}');
    }
  }

  static Future<Map<String, dynamic>> listAssignments({
    required String classId,
    String? token,
  }) async {
    final headers = {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
    final response = await http.get(
      Uri.parse('$baseUrl/classes/$classId/assignments'),
      headers: headers,
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('List assignments failed: ${response.body}');
    }
  }

  static Future<Map<String, dynamic>> createAssignment({
    required String classId,
    required String title,
    String? description,
    String? dueDate,
    String? token,
  }) async {
    final headers = {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
    final body = jsonEncode({
      'title': title,
      if (description != null) 'description': description,
      if (dueDate != null) 'due_date': dueDate,
    });
    final response = await http.post(
      Uri.parse('$baseUrl/classes/$classId/assignments'),
      headers: headers,
      body: body,
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Create assignment failed: ${response.body}');
    }
  }

  static Future<void> updateProfile({
    required String role,
    required String university,
    required String state,
    String? token,
    String? email,
  }) async {
    final headers = {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
    final body = jsonEncode({
      'role': role,
      'university': university,
      'state': state,
    });
    final uri = Uri.parse('$baseUrl/users/me').replace(queryParameters: {
      if (email != null) 'email': email,
    });
    final response = await http.put(
      uri,
      headers: headers,
      body: body,
    );
    if (response.statusCode != 200) {
      throw Exception('Update profile failed: ${response.body}');
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

  static Future<Map<String, dynamic>> getClassGradesForStudent({
    required String classId,
    required String studentId,
    String? token,
  }) async {
    final headers = {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
    final response = await http.get(
      Uri.parse('$baseUrl/classes/$classId/grades/student/$studentId'),
      headers: headers,
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Get student grades failed: ${response.body}');
    }
  }

  static Future<void> setStudentGrade({
    required String classId,
    required String assignmentId,
    required String studentId,
    required double grade,
    String? token,
  }) async {
    final headers = {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
    final body = jsonEncode({
      'assignment_id': assignmentId,
      'grade': grade,
    });
    final uri = Uri.parse('$baseUrl/classes/$classId/grades/set')
        .replace(queryParameters: {'student_id': studentId});
    final response = await http.post(
      uri,
      headers: headers,
      body: body,
    );
    if (response.statusCode != 200) {
      throw Exception('Set grade failed: ${response.body}');
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