import { describe, expect, it } from 'vitest';
import {
  TARGET_FIELDS,
  suggestFieldMap,
  requiredFields,
  isFieldMapComplete,
} from '../mapping';

describe('ingestion mapping utilities', () => {
  it('suggests mappings for ADP payroll exports using synonyms', () => {
    const headers = [
      'Associate ID',
      'Associate Name',
      'Department',
      'Job Title',
      'Work Location',
      'Pay Period Start',
      'Pay Period End',
      'Pay Date',
      'Regular Hours',
      'OT Hours',
      'Gross Wages',
      'Net Amount',
      'Tax Withholding',
      'Employer Taxes',
      'Employee Deductions',
    ];

    const map = suggestFieldMap(headers, 'adp', 'payroll', 'payroll');

    expect(map.employeeId).toBe('Associate ID');
    expect(map.employeeName).toBe('Associate Name');
    expect(map.department).toBe('Department');
    expect(map.position).toBe('Job Title');
    expect(map.locationName).toBe('Work Location');
    expect(map.payPeriodStart).toBe('Pay Period Start');
    expect(map.payPeriodEnd).toBe('Pay Period End');
    expect(map.payDate).toBe('Pay Date');
    expect(map.hoursWorked).toBe('Regular Hours');
    expect(map.overtimeHours).toBe('OT Hours');
    expect(map.grossPay).toBe('Gross Wages');
    expect(map.netPay).toBe('Net Amount');
    expect(map.taxes).toBe('Tax Withholding');
    expect(map.employerTaxes).toBe('Employer Taxes');
    expect(map.deductions).toBe('Employee Deductions');
  });

  it('infers NetSuite monthly financial headers by dataset', () => {
    const headers = [
      'Period',
      'Start Date',
      'End Date',
      'Subsidiary',
      'Total Revenue',
      'Total Expenses',
      'Net Income',
      'EBITDA',
      'Gross Margin',
      'Payroll Expense',
      'Cash Balance',
      'Accounts Receivable',
      'Accounts Payable',
      'Other Income',
    ];

    const map = suggestFieldMap(headers, 'netsuite', 'financials', 'financials');

    expect(map.periodLabel).toBe('Period');
    expect(map.periodStart).toBe('Start Date');
    expect(map.periodEnd).toBe('End Date');
    expect(map.locationName).toBe('Subsidiary');
    expect(map.totalRevenue).toBe('Total Revenue');
    expect(map.totalExpenses).toBe('Total Expenses');
    expect(map.netIncome).toBe('Net Income');
    expect(map.ebitda).toBe('EBITDA');
    expect(map.grossMargin).toBe('Gross Margin');
    expect(map.payrollExpense).toBe('Payroll Expense');
    expect(map.cashBalance).toBe('Cash Balance');
    expect(map.arBalance).toBe('Accounts Receivable');
    expect(map.apBalance).toBe('Accounts Payable');
    expect(map.otherIncome).toBe('Other Income');
  });

  it('validates required fields per target before promotion', () => {
    expect(requiredFields('payroll')).toEqual(['employeeName', 'grossPay']);
    expect(requiredFields('financials')).toEqual(['totalRevenue']);

    const payrollMap = { employeeName: 'Associate Name', grossPay: 'Gross Wages' };
    expect(isFieldMapComplete(payrollMap, 'payroll')).toBe(true);

    const incomplete = { employeeName: 'Associate Name', grossPay: '' };
    expect(isFieldMapComplete(incomplete, 'payroll')).toBe(false);
  });

  it('falls back to empty strings when headers missing to assist UI display', () => {
    const map = suggestFieldMap([], 'dentrix', 'patients', 'patients');

    TARGET_FIELDS.patients.forEach((field) => {
      expect(map[field]).toBe('');
    });
  });
});
