import 'package:flutter/material.dart';
import 'app_bottom_nav.dart';

class AccountPage extends StatelessWidget {
  const AccountPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Account')),
      body: const Center(child: Text('Account Page')),
      bottomNavigationBar: AppBottomNav(currentIndex: 4),
    );
  }
}


