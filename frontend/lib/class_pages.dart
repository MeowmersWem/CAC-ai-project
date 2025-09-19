import 'package:flutter/material.dart';
import 'in_class_page.dart';

class EnglishClassPage extends StatelessWidget {
  const EnglishClassPage({super.key});

  @override
  Widget build(BuildContext context) => const InClassPage(className: 'English');
}

class MathClassPage extends StatelessWidget {
  const MathClassPage({super.key});

  @override
  Widget build(BuildContext context) => const InClassPage(className: 'Math');
}

class CSClassPage extends StatelessWidget {
  const CSClassPage({super.key});

  @override
  Widget build(BuildContext context) => const InClassPage(className: 'CS');
}

class ChemistryClassPage extends StatelessWidget {
  const ChemistryClassPage({super.key});

  @override
  Widget build(BuildContext context) => const InClassPage(className: 'Chemistry');
}

class SixSevenClassPage extends StatelessWidget {
  const SixSevenClassPage({super.key});

  @override
  Widget build(BuildContext context) => const InClassPage(className: 'SixSeven');
}


