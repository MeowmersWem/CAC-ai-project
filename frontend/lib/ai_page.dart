import 'package:flutter/material.dart';
import 'app_bottom_nav.dart';

class AIPage extends StatelessWidget {
  const AIPage({super.key});

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('AI')),
      body: const Center(child: Text('AI Page')),
      bottomNavigationBar: const AppBottomNav(currentIndex: 1),
    );
  }
}


