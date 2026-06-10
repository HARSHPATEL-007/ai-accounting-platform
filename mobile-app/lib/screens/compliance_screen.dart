import 'package:flutter/material.dart';
import 'package:accounting_platform_mobile/models/compliance_item.dart';

class ComplianceScreen extends StatelessWidget {
  const ComplianceScreen({super.key});

  final List<ComplianceItem> _items = const [
    ComplianceItem(
      id: '1',
      title: 'GSTR-1 Filing (June 2024)',
      dueDate: null,
      status: ComplianceStatus.pending,
      type: ComplianceType.gst,
      progress: 75,
      description: 'Upload all B2B and B2C invoices',
    ),
    ComplianceItem(
      id: '2',
      title: 'GSTR-3B Filing (June 2024)',
      dueDate: null,
      status: ComplianceStatus.pending,
      type: ComplianceType.gst,
      progress: 60,
      description: 'Summary return with tax payment',
    ),
    ComplianceItem(
      id: '3',
      title: 'TDS Return Q1',
      dueDate: null,
      status: ComplianceStatus.inProgress,
      type: ComplianceType.tds,
      progress: 40,
      description: 'Quarterly TDS statement',
    ),
  ];

  Color _getStatusColor(ComplianceStatus status) {
    switch (status) {
      case ComplianceStatus.completed:
        return Colors.green;
      case ComplianceStatus.pending:
        return Colors.orange;
      case ComplianceStatus.overdue:
        return Colors.red;
      case ComplianceStatus.inProgress:
        return Colors.blue;
    }
  }

  IconData _getTypeIcon(ComplianceType type) {
    switch (type) {
      case ComplianceType.gst:
        return Icons.receipt;
      case ComplianceType.tax:
        return Icons.account_balance;
      case ComplianceType.tds:
        return Icons.money_off;
      case ComplianceType.audit:
        return Icons.search;
      case ComplianceType.roc:
        return Icons.business;
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _items.length,
      itemBuilder: (context, index) {
        final item = _items[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(_getTypeIcon(item.type), color: _getStatusColor(item.status)),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            item.title,
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                          ),
                          Text(
                            item.description ?? '',
                            style: TextStyle(color: Colors.grey[600], fontSize: 14),
                          ),
                        ],
                      ),
                    ),
                    Chip(
                      label: Text(
                        item.status.name.toUpperCase(),
                        style: const TextStyle(fontSize: 10, color: Colors.white),
                      ),
                      backgroundColor: _getStatusColor(item.status),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                LinearProgressIndicator(
                  value: item.progress / 100,
                  backgroundColor: Colors.grey[200],
                  valueColor: AlwaysStoppedAnimation<Color>(_getStatusColor(item.status)),
                ),
                const SizedBox(height: 4),
                Text(
                  '${item.progress.toInt()}% complete',
                  style: TextStyle(color: Colors.grey[600], fontSize: 12),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
