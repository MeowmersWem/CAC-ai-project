import 'package:flutter/material.dart';
import 'app_bottom_nav.dart';

class GradesPage extends StatelessWidget {
  const GradesPage({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      appBar: AppBar(title: Text('Grades')),
      body: Center(child: Text('Grades Page')),
      bottomNavigationBar: AppBottomNav(currentIndex: 2),
    );
  }
}


