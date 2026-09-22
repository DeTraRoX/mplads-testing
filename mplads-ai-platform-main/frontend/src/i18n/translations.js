export const translations = {
  en: {
    // Navigation
    executiveDashboard: 'Executive Dashboard',
    geospatialIntelligence: 'Geospatial Intelligence',
    top5HighRisk: 'Top 5% High-Risk Works',
    auditDesk: 'Interactive Audit Desk',
    liveAnalyzer: 'Live Proposal Analyzer',

    // Dashboard
    totalProjects: 'Total Projects',
    criticalProjects: 'Critical Projects',
    highRiskProjects: 'High-Risk Projects',
    priorityProjects: 'Top 5% Priority Projects',
    paymentMismatch: 'Payment-Progress Mismatch',
    geospatialAnomalies: 'Geospatial Anomalies',
    duplicateEvidence: 'Duplicate Evidence',
    duplicateProjects: 'Duplicate Projects',
    timelineDelays: 'Timeline Delays',
    casesUnderReview: 'Cases Under Review',
    casesResolved: 'Cases Resolved',
    flaggedExpenditure: 'Flagged Expenditure Outlay',

    // Common
    loading: 'Loading',
    search: 'Search',
    filter: 'Filter',
    export: 'Export',
    inspect: 'Inspect',
    severity: 'Severity',
    district: 'District',
    riskScore: 'Risk Score',

    // Map
    mapLegend: 'Map Legend',
    geoDeviation: 'Geo Deviation Vector',
    displaying: 'Displaying',
    flaggedWorks: 'flagged works',
    loadingGeospatial: 'Loading geospatial data...',

    // Severity levels
    critical: 'CRITICAL',
    high: 'HIGH',
    medium: 'MEDIUM',
    low: 'LOW',

    // Roles
    centralAdmin: 'Central Admin (MoSPI)',
    districtOfficer: 'District Officer',
    leadAuditor: 'Lead Auditor (CAG)',

    // Actions
    openForensicDesk: 'Open Forensic Desk',
    exportForensicCSV: 'Export Forensic CSV',
    reseedData: 'Re-Seed Data',

    // Badges
    govStandard: '🇮🇳 MoSPI / GOI Standard',
    realtime: 'Real-time',
    gis: 'GIS',
    priority: 'Priority',
    hitl: 'HITL',
    sih: 'SIH',
  },
  hi: {
    // Navigation
    executiveDashboard: 'कार्यकारी डैशबोर्ड',
    geospatialIntelligence: 'भू-स्थानिक खुफिया',
    top5HighRisk: 'शीर्ष 5% उच्च जोखिम कार्य',
    auditDesk: 'इंटरैक्टिव ऑडिट डेस्क',
    liveAnalyzer: 'लाइव प्रस्ताव विश्लेषक',

    // Dashboard
    totalProjects: 'कुल परियोजनाएं',
    criticalProjects: 'गंभीर परियोजनाएं',
    highRiskProjects: 'उच्च जोखिम परियोजनाएं',
    priorityProjects: 'शीर्ष 5% प्राथमिकता परियोजनाएं',
    paymentMismatch: 'भुगतान-प्रगति बेमेल',
    geospatialAnomalies: 'भू-स्थानिक विसंगतियां',
    duplicateEvidence: 'डुप्लिकेट साक्ष्य',
    duplicateProjects: 'डुप्लिकेट परियोजनाएं',
    timelineDelays: 'समयरेखा में देरी',
    casesUnderReview: 'समीक्षाधीन मामले',
    casesResolved: 'हल किए गए मामले',
    flaggedExpenditure: 'चिह्नित व्यय परिव्यय',

    // Common
    loading: 'लोड हो रहा है',
    search: 'खोजें',
    filter: 'फ़िल्टर',
    export: 'निर्यात',
    inspect: 'निरीक्षण करें',
    severity: 'गंभीरता',
    district: 'जिला',
    riskScore: 'जोखिम स्कोर',

    // Map
    mapLegend: 'मानचित्र लीजेंड',
    geoDeviation: 'भू विचलन वेक्टर',
    displaying: 'प्रदर्शित हो रहा है',
    flaggedWorks: 'चिह्नित कार्य',
    loadingGeospatial: 'भू-स्थानिक डेटा लोड हो रहा है...',

    // Severity levels
    critical: 'गंभीर',
    high: 'उच्च',
    medium: 'मध्यम',
    low: 'निम्न',

    // Roles
    centralAdmin: 'केंद्रीय प्रशासक (MoSPI)',
    districtOfficer: 'जिला अधिकारी',
    leadAuditor: 'मुख्य लेखा परीक्षक (CAG)',

    // Actions
    openForensicDesk: 'फोरेंसिक डेस्क खोलें',
    exportForensicCSV: 'फोरेंसिक CSV निर्यात करें',
    reseedData: 'डेटा पुनः बीज',

    // Badges
    govStandard: '🇮🇳 MoSPI / भारत सरकार मानक',
    realtime: 'वास्तविक समय',
    gis: 'GIS',
    priority: 'प्राथमिकता',
    hitl: 'HITL',
    sih: 'SIH',
  }
};

export const useTranslation = (language) => {
  return (key) => translations[language]?.[key] || translations.en[key] || key;
};
