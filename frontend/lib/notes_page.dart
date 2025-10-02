import 'package:flutter/material.dart';
import 'app_bottom_nav.dart';

class NotesPage extends StatelessWidget {
  const NotesPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Notes')),
      body: const Center(child: Text('Notes Page')),
      bottomNavigationBar: AppBottomNav(currentIndex: 3),
    );
  }
}


