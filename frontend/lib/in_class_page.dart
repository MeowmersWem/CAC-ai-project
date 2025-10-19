import 'package:flutter/material.dart';
import 'app_bottom_nav.dart';
import 'student_assignments_page.dart';
import 'student_classmates_page.dart';
import 'teacher_students_page.dart';
import 'student_grades_page.dart';
import 'services/api_service.dart';

class InClassPage extends StatefulWidget {
  const InClassPage({super.key, required this.classId, required this.className});

  final String classId;
  final String className;

  @override
  State<InClassPage> createState() => _InClassPageState();
}

class _InClassPageState extends State<InClassPage> {
  bool _showComposer = false;
  final TextEditingController _postController = TextEditingController();
  Map<String, dynamic>? _classDetails; // includes join_code for instructors
  bool _loadingDetails = true;

  @override
  void dispose() {
    _postController.dispose();
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    _loadDetails();
  }

  Future<void> _loadDetails() async {
    try {
      final details = await ApiService.getClassDetails(classId: widget.classId);
      if (!mounted) return;
      setState(() {
        _classDetails = details;
        _loadingDetails = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() { _loadingDetails = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final ColorScheme scheme = theme.colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.className),
        backgroundColor: scheme.inversePrimary,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (_loadingDetails)
                const LinearProgressIndicator(minHeight: 2),
              if (!_loadingDetails && (_classDetails?['join_code'] != null)) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.grey.shade300),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.key_outlined),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'Join code: ${_classDetails!['join_code']}',
                          style: const TextStyle(fontWeight: FontWeight.w600),
                        ),
                      ),
                      IconButton(
                        tooltip: 'Copy',
                        onPressed: () {
                          final code = (_classDetails!['join_code'] ?? '').toString();
                          if (code.isEmpty) return;
                          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Copied join code')));
                        },
                        icon: const Icon(Icons.copy_all_outlined),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],
              SizedBox(
                height: 48,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.black,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    textStyle: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  onPressed: () {
                    setState(() {
                      _showComposer = true;
                    });
                  },
                  child: const Text('New Post'),
                ),
              ),
              const SizedBox(height: 12),
              if (_showComposer) ...[
                TextField(
                  controller: _postController,
                  maxLines: 6,
                  decoration: InputDecoration(
                    hintText: 'Write your post here...',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    filled: true,
                    fillColor: Colors.white,
                    contentPadding: const EdgeInsets.all(12),
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton(
                        onPressed: () {
                          // Placeholder for submit action
                          FocusScope.of(context).unfocus();
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('Post submitted')),
                          );
                          setState(() {
                            _showComposer = false;
                            _postController.clear();
                          });
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.black,
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                        child: const Text('Submit'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: OutlinedButton(
                        onPressed: () {
                          setState(() {
                            _showComposer = false;
                            _postController.clear();
                          });
                        },
                        style: OutlinedButton.styleFrom(
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                        child: const Text('Cancel'),
                      ),
                    ),
                  ],
                ),
              ],
              const SizedBox(height: 24),
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: Colors.black,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                          side: BorderSide(color: Colors.grey.shade300),
                        ),
                      ),
                      onPressed: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => StudentClassmatesPage(classId: widget.classId),
                          ),
                        );
                      },
                      child: const Text('Classmates'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: Colors.black,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                          side: BorderSide(color: Colors.grey.shade300),
                        ),
                      ),
                      onPressed: () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('AI Study coming soon...')),
                        );
                      },
                      child: const Text('My Students (instructor)'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              // Large buttons: Lesson Notes and Assignments
              SizedBox(
                height: 72,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.white,
                    foregroundColor: Colors.black,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                      side: BorderSide(color: Colors.grey.shade300),
                    ),
                    textStyle: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Opening Lesson Notes...')),
                    );
                  },
                  child: const Text('Lesson Notes'),
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                height: 72,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.white,
                    foregroundColor: Colors.black,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                      side: BorderSide(color: Colors.grey.shade300),
                    ),
                    textStyle: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                      onPressed: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => TeacherStudentsPage(classId: widget.classId),
                          ),
                        );
                      },
                  child: const Text('Assignments'),
                ),
              ),
              const SizedBox(height: 24),
              // Bottom Grades button
              SizedBox(
                height: 56,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: scheme.primary,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    textStyle: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  onPressed: () async {
                    final profile = await ApiService.getProfile();
                    final String studentId = (profile['user_id'] ?? '').toString();
                    if (!mounted || studentId.isEmpty) return;
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => StudentGradesPage(
                          classId: widget.classId,
                          studentId: studentId,
                        ),
                      ),
                    );
                  },
                  child: const Text('Grades'),
                ),
              ),
            ],
          ),
        ),
      ),
      bottomNavigationBar: const AppBottomNav(currentIndex: 0),
    );
  }
}


