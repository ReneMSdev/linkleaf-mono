import 'package:flutter/material.dart';
import '../models/link.dart';

class LinkTile extends StatelessWidget {
  final Link link;

  const LinkTile({super.key, required this.link});

  @override
  Widget build(BuildContext context) {
    return ListTile(title: Text(link.title), subtitle: Text(link.url));
  }
}
