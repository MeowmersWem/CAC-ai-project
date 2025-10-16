import 'package:flutter/material.dart';
import 'app_bottom_nav.dart';
import 'services/api_service.dart';
import 'main.dart';

class AccountPage extends StatelessWidget {
  const AccountPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Account')),
      body: Center(
        child: SizedBox(
          height: 44,
          child: ElevatedButton(
            onPressed: () async {
              try {
                await ApiService.signOut();
              } catch (_) {}
              if (!context.mounted) return;
              Navigator.of(context).pushAndRemoveUntil(
                MaterialPageRoute(builder: (_) => const MyApp()),
                (route) => false,
              );
            },
            child: const Text('Sign out'),
          ),
        ),
      ),
      bottomNavigationBar: const AppBottomNav(currentIndex: 4),
    );
  }
}


