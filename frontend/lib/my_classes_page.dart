import 'package:flutter/material.dart';
import 'in_class_page.dart';
import 'app_bottom_nav.dart';

class MyClassesPage extends StatelessWidget {
  const MyClassesPage({super.key});

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final ColorScheme scheme = theme.colorScheme;

    // Base button height is 48 in the app; make each class tile 4x that => 192.
    const double tileHeight = 192;
    final List<String> classes = const [
      'English',
      'Math',
      'CS',
      'Chemistry',
      'SixSeven',
    ];

    String _routeFor(String label) {
      switch (label.toLowerCase()) {
        case 'english':
          return '/in-class/english';
        case 'math':
          return '/in-class/math';
        case 'cs':
          return '/in-class/cs';
        case 'chemistry':
          return '/in-class/chemistry';
        case 'sixseven':
          return '/in-class/sixseven';
        default:
          return '/in-class';
      }
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('My Classes'),
        backgroundColor: scheme.inversePrimary,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              SizedBox(
                height: 44,
                child: ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: scheme.primary,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                    textStyle: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  onPressed: () => Navigator.of(context).pushNamed('/class-search'),
                  icon: const Icon(Icons.add),
                  label: const Text('Add Classes'),
                ),
              ),
              const SizedBox(height: 12),
              Expanded(
                child: ListView.separated(
                  padding: EdgeInsets.zero,
                  itemCount: classes.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 12),
                  itemBuilder: (context, index) {
                    final String label = classes[index];
                    return SizedBox(
                      height: tileHeight,
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.white,
                          foregroundColor: Colors.black,
                          elevation: 2,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                            side: BorderSide(color: Colors.grey.shade300),
                          ),
                          textStyle: const TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        onPressed: () => Navigator.of(context).pushNamed(_routeFor(label)),
                        child: Text(label),
                      ),
                    );
                  },
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


