import 'package:flutter/material.dart';

class AppBottomNav extends StatelessWidget {
  const AppBottomNav({super.key, required this.currentIndex});

  final int currentIndex; // 0: Home, 1: AI, 2: Grades, 3: Notes, 4: Account

  @override
  Widget build(BuildContext context) {
    return BottomNavigationBar(
      type: BottomNavigationBarType.fixed,
      currentIndex: currentIndex,
      onTap: (int index) {
        if (index == currentIndex) return;
        final String route = switch (index) {
          0 => '/my-classes',
          1 => '/ai',
          2 => '/grades',
          3 => '/notes',
          4 => '/account',
          _ => '/my-classes',
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


