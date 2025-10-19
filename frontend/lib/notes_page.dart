import 'package:flutter/material.dart';
import 'app_bottom_nav.dart';
import 'instructor_bottom_nav.dart';

class NotesPage extends StatelessWidget {
  const NotesPage({super.key, this.isInstructor = false});
  final bool isInstructor;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Notes')),
      body: const Center(child: Text('Notes Page')),
      bottomNavigationBar: isInstructor
          ? const InstructorBottomNav(currentIndex: 3)
          : const AppBottomNav(currentIndex: 3),
    );
  }
}


