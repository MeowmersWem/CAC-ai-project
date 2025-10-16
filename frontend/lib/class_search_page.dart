import 'package:flutter/material.dart';
import 'services/api_service.dart';

class ClassSearchPage extends StatefulWidget {
  const ClassSearchPage({super.key});

  @override
  State<ClassSearchPage> createState() => _ClassSearchPageState();
}

class _ClassSearchPageState extends State<ClassSearchPage> {
  final TextEditingController _classNameController = TextEditingController();
  final TextEditingController _teacherNameController = TextEditingController();
  final TextEditingController _joinCodeController = TextEditingController();
  final TextEditingController _emailController = TextEditingController();
  bool _joining = false;

  @override
  void dispose() {
    _classNameController.dispose();
    _teacherNameController.dispose();
    _joinCodeController.dispose();
    _emailController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final ColorScheme scheme = theme.colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Search Classes'),
        backgroundColor: scheme.inversePrimary,
        actions: [
          IconButton(
            icon: const Icon(Icons.home_outlined),
            tooltip: 'My Classes',
            onPressed: () {
              Navigator.of(context).pushNamed('/my-classes');
            },
          ),
        ],
      ),
      body: SafeArea(
        child: Container(
          width: double.infinity,
          height: double.infinity,
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'Find your class',
                style: theme.textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 16),
              _DecoratedField(
                controller: _classNameController,
                labelText: 'Class name',
                icon: Icons.class_,
                textInputAction: TextInputAction.next,
              ),
              const SizedBox(height: 12),
              _DecoratedField(
                controller: _teacherNameController,
                labelText: 'Teacher name',
                icon: Icons.person_outline,
                textInputAction: TextInputAction.done,
              ),
              const SizedBox(height: 12),
              SizedBox(
                height: 56,
                child: ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: scheme.primary,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    textStyle: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  onPressed: () {
                    Navigator.of(context).pushNamed('/my-classes');
                  },
                  icon: const Icon(Icons.class_),
                  label: const Text('My Classes'),
                ),
              ),
              const SizedBox(height: 24),
              Text(
                'Have a code? Join a class',
                style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 8),
              _DecoratedField(
                controller: _joinCodeController,
                labelText: 'Class code (e.g., ABC123)',
                icon: Icons.key_outlined,
                textInputAction: TextInputAction.next,
              ),
              const SizedBox(height: 8),
              _DecoratedField(
                controller: _emailController,
                labelText: 'Your email',
                icon: Icons.email_outlined,
                textInputAction: TextInputAction.done,
              ),
              const SizedBox(height: 12),
              SizedBox(
                height: 56,
                child: ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.black,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    textStyle: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  onPressed: _joining ? null : _onJoinPressed,
                  icon: _joining
                      ? const SizedBox(height: 16, width: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                      : const Icon(Icons.login),
                  label: const Text('Join with code'),
                ),
              ),
              const Spacer(),
              SizedBox(
                height: 56,
                child: ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.black,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    textStyle: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  onPressed: _onSearchPressed,
                  icon: const Icon(Icons.search),
                  label: const Text('Search'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _onSearchPressed() {
    final String className = _classNameController.text.trim();
    final String teacherName = _teacherNameController.text.trim();
    // TODO: Hook this up to your actual search logic.
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Searching for "$className" with "$teacherName"'),
      ),
    );
  }

  Future<void> _onJoinPressed() async {
    final code = _joinCodeController.text.trim();
    final email = _emailController.text.trim();
    if (code.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Enter a class code')),
      );
      return;
    }
    setState(() { _joining = true; });
    try {
      await ApiService.joinClass(classCode: code, email: email.isEmpty ? null : email);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Joined class!')),
      );
      Navigator.of(context).pushNamed('/my-classes');
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to join: ${e.toString()}')),
      );
    } finally {
      if (mounted) setState(() { _joining = false; });
    }
  }
}

class _DecoratedField extends StatelessWidget {
  final TextEditingController controller;
  final String labelText;
  final IconData icon;
  final TextInputAction textInputAction;

  const _DecoratedField({
    required this.controller,
    required this.labelText,
    required this.icon,
    required this.textInputAction,
  });

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      textInputAction: textInputAction,
      decoration: InputDecoration(
        labelText: labelText,
        prefixIcon: Icon(icon),
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Colors.grey.shade300),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Colors.black, width: 1.2),
        ),
        isDense: true,
        contentPadding: const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
      ),
    );
  }
}



