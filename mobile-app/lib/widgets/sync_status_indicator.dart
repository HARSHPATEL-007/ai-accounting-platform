import 'package:flutter/material.dart';
import 'package:accounting_platform_mobile/services/sync_service.dart';

class SyncStatusIndicator extends StatefulWidget {
  const SyncStatusIndicator({super.key});

  @override
  State<SyncStatusIndicator> createState() => _SyncStatusIndicatorState();
}

class _SyncStatusIndicatorState extends State<SyncStatusIndicator> {
  final SyncService _syncService = SyncService();
  SyncStatus _currentStatus = SyncStatus.synced;
  int _pendingCount = 0;

  @override
  void initState() {
    super.initState();
    _syncService.syncStream.listen((status) {
      setState(() => _currentStatus = status);
    });
    _loadPendingCount();
  }

  Future<void> _loadPendingCount() async {
    final pending = await _syncService.getPendingDocuments();
    setState(() => _pendingCount = pending.length);
  }

  @override
  Widget build(BuildContext context) {
    IconData icon;
    Color color;

    switch (_currentStatus) {
      case SyncStatus.synced:
        icon = Icons.cloud_done;
        color = Colors.green;
        break;
      case SyncStatus.pending:
        icon = Icons.cloud_queue;
        color = Colors.orange;
        break;
      case SyncStatus.processing:
        icon = Icons.sync;
        color = Colors.blue;
        break;
      case SyncStatus.failed:
        icon = Icons.cloud_off;
        color = Colors.red;
        break;
    }

    return Row(
      children: [
        if (_pendingCount > 0)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: Colors.orange,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Text(
              '$_pendingCount',
              style: const TextStyle(color: Colors.white, fontSize: 12),
            ),
          ),
        const SizedBox(width: 4),
        Icon(icon, color: color, size: 20),
      ],
    );
  }
}
