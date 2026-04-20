import 'package:flutter/material.dart';
import '../models/profile.dart';

class ProfileCard extends StatelessWidget {
  final Profile profile;

  const ProfileCard({super.key, required this.profile});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Text(profile.displayName, style: Theme.of(context).textTheme.headlineSmall),
      ),
    );
  }
}
