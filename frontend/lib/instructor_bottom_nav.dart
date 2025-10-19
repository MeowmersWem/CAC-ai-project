import 'package:flutter/material.dart';

class InstructorBottomNav extends StatelessWidget {
  const InstructorBottomNav({super.key, required this.currentIndex});

  final int currentIndex; // 0: Home, 1: AI, 2: Grades, 3: Notes, 4: Account

  @override
  Widget build(BuildContext context) {
    return BottomNavigationBar(
      type: BottomNavigationBarType.fixed,
      currentIndex: currentIndex,
      onTap: (int index) {
        if (index == currentIndex) return;
        final String route = switch (index) {
          0 => '/instructor/my-classes',
          1 => '/instructor/ai',
          2 => '/instructor/grades',
          3 => '/instructor/notes',
          4 => '/instructor/account',
          _ => '/instructor/my-classes',
        };
        Navigator.of(context).pushReplacementNamed(route);
      },
      items: const [
        BottomNavigationBarItem(icon: Icon(Icons.home_outlined), label: 'Home'),
        BottomNavigationBarItem(icon: Icon(Icons.smart_toy_outlined), label: 'AI'),
        BottomNavigationBarItem(icon: Icon(Icons.grading_outlined), label: 'Grades'),
        BottomNavigationBarItem(icon: Icon(Icons.notes_outlined), label: 'Notes'),
        BottomNavigationBarItem(icon: Icon(Icons.person_outline), label: 'Account'),
      ],
    );
  }
}


