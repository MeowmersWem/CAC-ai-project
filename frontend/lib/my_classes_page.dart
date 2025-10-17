import 'package:flutter/material.dart';
import 'app_bottom_nav.dart';
import 'in_class_page.dart';
import 'services/api_service.dart';

class MyClassesPage extends StatelessWidget {
  const MyClassesPage({super.key});

  Future<List<Map<String, dynamic>>> _load() async {
    final res = await ApiService.getUserClasses();
    final List<dynamic> items = res['classes'] ?? [];
    return items.cast<Map<String, dynamic>>();
  }

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final ColorScheme scheme = theme.colorScheme;

    const double tileHeight = 192;

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
                  label: const Text('Join Classes'),
                ),
              ),
              const SizedBox(height: 12),
              Expanded(
                child: FutureBuilder<List<Map<String, dynamic>>>(
                  future: _load(),
                  builder: (context, snap) {
                    if (snap.connectionState != ConnectionState.done) {
                      return const Center(child: CircularProgressIndicator());
                    }
                    if (snap.hasError) {
                      return Center(child: Text('Error: ${snap.error}'));
                    }
                    final classes = snap.data ?? const [];
                    if (classes.isEmpty) {
                      return Center(
                        child: Text(
                          'No classes yet. Create one or join with a code.',
                          style: Theme.of(context).textTheme.bodyLarge,
                        ),
                      );
                    }
                    return ListView.separated(
                      padding: EdgeInsets.zero,
                      itemCount: classes.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 12),
                      itemBuilder: (context, index) {
                        final item = classes[index];
                        final String name = (item['name'] ?? 'Class') as String;
                        final String classId = (item['class_id'] ?? '') as String;
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
                            onPressed: () => Navigator.of(context).push(
                              MaterialPageRoute(
                                builder: (_) => InClassPage(classId: classId, className: name),
                              ),
                            ),
                            child: Text(name),
                          ),
                        );
                      },
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


