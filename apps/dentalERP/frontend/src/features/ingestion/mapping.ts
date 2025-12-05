// Utility and presets to help map source CSV/PDF/JSON headers to canonical target fields
// for manual ingestion flows (patients, payroll, financials, etc.).

export type IngestionTarget = 'patients' | 'payroll' | 'financials' | 'dentrix_day_sheet' | 'eaglesoft_day_sheet';
export type SourceSystem = 'dentrix' | 'dentalintel' | 'adp' | 'eaglesoft' | 'netsuite' | 'quickbooks';
export type Dataset = 'unknown' | 'patients' | 'appointments' | 'payroll' | 'financials' | 'day_sheet';

// Canonical field sets per target
export const TARGET_FIELDS: Record<IngestionTarget, string[]> = {
  patients: ['externalId', 'firstName', 'lastName', 'email', 'phone', 'dateOfBirth', 'gender', 'notes'],
  payroll: [
    'externalId',
    'employeeId',
    'employeeName',
    'department',
    'position',
    'locationName',
    'payPeriodStart',
    'payPeriodEnd',
    'payDate',
    'hoursWorked',
    'overtimeHours',
    'grossPay',
    'netPay',
    'taxes',
    'benefits',
    'deductions',
    'employerTaxes',
    'currency',
    'notes',
  ],
  financials: [
    'periodLabel',
    'periodStart',
    'periodEnd',
    'locationName',
    'currency',
    'totalRevenue',
    'totalExpenses',
    'netIncome',
    'ebitda',
    'grossMargin',
    'payrollExpense',
    'cashBalance',
    'arBalance',
    'apBalance',
    'otherIncome',
    'notes',
  ],
  dentrix_day_sheet: [],
  eaglesoft_day_sheet: [],
};

// Header synonyms per source system and dataset → canonical field → list of common header names
const SOURCE_SYNONYMS: Record<SourceSystem, Partial<Record<Dataset | IngestionTarget, Record<string, string[]>>>> = {
  dentrix: {
    patients: {
      externalId: ['patient id', 'patientid', 'chart number', 'chartnumber', 'patnum', 'guarantor id'],
      firstName: ['first name', 'firstname', 'first', 'given name', 'fname'],
      lastName: ['last name', 'lastname', 'last', 'surname', 'lname'],
      email: ['email', 'e-mail', 'email address'],
      phone: ['phone', 'phone number', 'cell', 'cell phone', 'mobile', 'mobile phone', 'home phone', 'work phone'],
      dateOfBirth: ['dob', 'date of birth', 'birthdate', 'birth date'],
      gender: ['gender', 'sex'],
      notes: ['notes', 'comments', 'patient notes'],
    },
  },
  dentalintel: {
    patients: {
      externalId: ['patient id', 'patientid', 'pt id', 'di patient id'],
      firstName: ['first name', 'firstname', 'pt first name'],
      lastName: ['last name', 'lastname', 'pt last name'],
      email: ['email', 'email address'],
      phone: ['phone', 'cell phone', 'mobile', 'mobile phone', 'home phone'],
      dateOfBirth: ['dob', 'date of birth', 'birthdate'],
      gender: ['gender', 'sex'],
      notes: ['notes', 'comments'],
    },
  },
  eaglesoft: {
    patients: {
      externalId: ['patient id', 'patientid', 'chart number', 'account #', 'account number'],
      firstName: ['first name', 'firstname'],
      lastName: ['last name', 'lastname'],
      email: ['email', 'email address'],
      phone: ['phone', 'home phone', 'work phone', 'mobile phone', 'cell'],
      dateOfBirth: ['dob', 'date of birth', 'birthdate'],
      gender: ['gender', 'sex'],
      notes: ['notes', 'comments'],
    },
  },
  adp: {
    patients: {
      externalId: ['associate id', 'employee id', 'person id'],
      firstName: ['first name', 'firstname'],
      lastName: ['last name', 'lastname'],
      email: ['email', 'work email', 'personal email'],
      phone: ['phone', 'mobile', 'home phone'],
      dateOfBirth: ['date of birth', 'dob', 'birthdate'],
      gender: ['gender', 'sex'],
      notes: ['notes', 'comments'],
    },
    payroll: {
      externalId: ['associate id', 'person number', 'payroll id'],
      employeeId: ['employee id', 'associate id', 'person id', 'worker id'],
      employeeName: ['associate name', 'employee name', 'worker name', 'name'],
      department: ['department', 'dept'],
      position: ['position', 'job title', 'title'],
      locationName: ['location', 'work location', 'branch'],
      payPeriodStart: ['pay period start', 'period start', 'start date'],
      payPeriodEnd: ['pay period end', 'period end', 'end date'],
      payDate: ['pay date', 'check date'],
      hoursWorked: ['hours', 'total hours', 'regular hours'],
      overtimeHours: ['overtime hours', 'ot hours'],
      grossPay: ['gross pay', 'gross wages', 'gross amount'],
      netPay: ['net pay', 'net amount'],
      taxes: ['taxes', 'tax withholding'],
      benefits: ['benefits', 'employer benefits', 'company benefits'],
      deductions: ['deductions', 'employee deductions'],
      employerTaxes: ['employer taxes', 'company taxes'],
      currency: ['currency'],
      notes: ['notes', 'comments'],
    },
  },
  netsuite: {
    financials: {
      periodLabel: ['period', 'accounting period', 'month'],
      periodStart: ['start date', 'period start'],
      periodEnd: ['end date', 'period end'],
      locationName: ['location', 'subsidiary', 'practice'],
      currency: ['currency'],
      totalRevenue: ['total revenue', 'revenue', 'income'],
      totalExpenses: ['total expenses', 'expenses', 'operating expenses'],
      netIncome: ['net income', 'net profit'],
      ebitda: ['ebitda'],
      grossMargin: ['gross margin', 'margin %', 'gross profit %'],
      payrollExpense: ['payroll expense', 'payroll'],
      cashBalance: ['cash balance', 'cash'],
      arBalance: ['accounts receivable', 'ar balance'],
      apBalance: ['accounts payable', 'ap balance'],
      otherIncome: ['other income'],
      notes: ['notes', 'memo'],
    },
  },
  quickbooks: {
    financials: {
      periodLabel: ['period', 'month', 'statement period'],
      periodStart: ['start date', 'from'],
      periodEnd: ['end date', 'to'],
      locationName: ['location', 'class', 'practice'],
      currency: ['currency'],
      totalRevenue: ['total income', 'total revenue', 'operating income'],
      totalExpenses: ['total expenses', 'expenses'],
      netIncome: ['net income', 'net operating income'],
      payrollExpense: ['payroll expense', 'wages'],
      cashBalance: ['cash', 'cash on hand'],
      arBalance: ['accounts receivable', 'a/r'],
      apBalance: ['accounts payable', 'a/p'],
      otherIncome: ['other income', 'non operating income'],
      notes: ['notes', 'memo'],
    },
  },
};

const normalize = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();

const unique = <T,>(arr: T[]) => Array.from(new Set(arr));

// Given available headers, suggest a fieldMap for a source/dataset/target
export function suggestFieldMap(
  headers: string[],
  sourceSystem: SourceSystem,
  dataset: Dataset,
  target: IngestionTarget = 'patients'
): Record<string, string> {
  const result: Record<string, string> = {};
  const canonical = TARGET_FIELDS[target];
  if (!headers || !headers.length) {
    canonical.forEach((f) => (result[f] = ''));
    return result;
  }

  const normalizedHeaders = headers.map((h) => ({ raw: h, norm: normalize(h) })).filter((h) => h.norm.length);
  const synonymSets = SOURCE_SYNONYMS[sourceSystem] || {};
  const datasetSynonyms = synonymSets[dataset] || {};
  const targetSynonyms = synonymSets[target] || {};

  for (const field of canonical) {
    const syns = unique([...(datasetSynonyms[field] || []), ...(targetSynonyms[field] || [])]).map(normalize).filter(Boolean);
    let mapped = '';

    for (const syn of syns) {
      const exact = normalizedHeaders.find((h) => h.norm === syn);
      if (exact) {
        mapped = exact.raw;
        break;
      }
    }

    if (!mapped) {
      const heuristics = [field, ...syns];
      const fuzzy = normalizedHeaders.find((h) => heuristics.some((k) => h.norm.includes(k)));
      if (fuzzy) mapped = fuzzy.raw;
    }

    result[field] = mapped;
  }

  return result;
}

export function requiredFields(target: IngestionTarget = 'patients'): string[] {
  if (target === 'patients') return ['firstName', 'lastName'];
  if (target === 'payroll') return ['employeeName', 'grossPay'];
  if (target === 'financials') return ['totalRevenue'];
  return [];
}

export function isFieldMapComplete(fieldMap: Record<string, string>, target: IngestionTarget = 'patients') {
  const req = requiredFields(target);
  return req.every((k) => (fieldMap?.[k] || '').trim().length > 0);
}
