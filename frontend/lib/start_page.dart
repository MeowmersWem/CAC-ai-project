import 'package:flutter/material.dart';
import 'services/api_service.dart';
import 'my_classes_page.dart';
import 'create_class_page.dart';

class StartPage extends StatefulWidget {
  const StartPage({super.key, required this.email});

  final String email;

  @override
  State<StartPage> createState() => _StartPageState();
}

class _StartPageState extends State<StartPage> {
  String _role = 'student';
  final TextEditingController _schoolController = TextEditingController();
  final List<String> _states = const [
    'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY'
  ];
  String? _selectedState;
  bool _submitting = false;
  String? _error;

  Future<void> _submit() async {
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      await ApiService.updateProfile(
        role: _role,
        university: _schoolController.text.trim(),
        state: (_selectedState ?? '').trim(),
        email: widget.email,
      );
      if (!mounted) return;
      if (_role == 'instructor') {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => CreateClassPage(email: widget.email)),
        );
      } else {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => const MyClassesPage()),
        );
      }
    } catch (e) {
      setState(() {
        _error = e.toString();
        _submitting = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final ColorScheme scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Welcome'),
        backgroundColor: scheme.inversePrimary,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'Tell us about you',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 16),
              const Text('Role'),
              Row(
                children: [
                  Expanded(
                    child: RadioListTile<String>(
                      value: 'student',
                      groupValue: _role,
                      onChanged: (v) => setState(() => _role = v ?? 'student'),
                      title: const Text('Student'),
                    ),
                  ),
                  Expanded(
                    child: RadioListTile<String>(
                      value: 'instructor',
                      groupValue: _role,
                      onChanged: (v) => setState(() => _role = v ?? 'instructor'),
                      title: const Text('Instructor'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _schoolController,
                decoration: const InputDecoration(
                  labelText: 'School / University',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: _selectedState,
                items: _states
                    .map((abbr) => DropdownMenuItem(value: abbr, child: Text(abbr)))
                    .toList(),
                onChanged: (v) => setState(() => _selectedState = v),
                decoration: const InputDecoration(
                  labelText: 'State',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              if (_error != null) ...[
                Text(_error!, style: const TextStyle(color: Colors.red)),
                const SizedBox(height: 8),
              ],
              SizedBox(
                height: 44,
                child: ElevatedButton(
                  onPressed: _submitting ? null : _submit,
                  child: _submitting
                      ? const SizedBox(
                          height: 16,
                          width: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Continue'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}


