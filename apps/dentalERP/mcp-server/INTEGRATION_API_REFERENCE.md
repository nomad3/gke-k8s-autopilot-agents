# Integration API Reference Guide

Comprehensive documentation for all external system integrations managed by MCP Server.

---

## 📚 Official Documentation Sources

### 1. **NetSuite SuiteTalk REST API** ✅

**Official Documentation:**
- **Getting Started**: https://docs.oracle.com/en/cloud/saas/netsuite-suiteprojects-pro/online-help/article_160000354697.html
- **REST API Guide**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/book_1559132836.html
- **API Browser**: https://system.netsuite.com/help/helpcenter/en_US/APIs/REST_API_Browser/record/v1/2022.1/index.html
- **Postman Tutorial**: https://www.postman.com/kennethjoseph/public/documentation/efis2w4/netsuite-rest-api-tutorial

**Key Details:**
- **Authentication**: OAuth 1.0a Token-Based Authentication (TBA)
- **Base URL**: `https://{account}.suitetalk.api.netsuite.com/services/rest/record/v1`
- **Rate Limits**: Max 1,000 objects per request
- **Signature Method**: HMAC-SHA256
- **Common Record Types**:
  - `journalEntry` - Financial transactions
  - `customer` - Customer records
  - `vendor` - Vendor records
  - `subsidiary` - Company subsidiaries
  - `employee` - Employee data

**Query Language:**
- **SuiteQL**: SQL-like syntax for efficient data retrieval
- **Filtering**: Use `q` parameter with boolean expressions
- **Field Selection**: Use `fields` parameter (comma-separated)

**Example Endpoints:**
```
GET /journalEntry?limit=100&fields=tranId,tranDate,amount
GET /customer?q=subsidiary.name=="Acme Corp"
GET /vendor?limit=50&offset=100
```

**Best Practices:**
- Test in sandbox environment first
- Handle rate limits with exponential backoff
- Use field selection to minimize response size
- Cache responses when appropriate
- Implement OAuth signature caching

**Implementation Status**: ✅ **Implemented** in `/mcp-server/src/connectors/netsuite.py`

---

### 2. **ADP Workforce Now API** ✅

**Official Documentation:**
- **Developer Portal**: https://developers.adp.com
- **API Reference**: https://developers.adp.com/articles/api/workforce-now-api
- **OAuth Guide**: https://developers.adp.com/articles/guide/auth-and-security

**Key Details:**
- **Authentication**: OAuth 2.0 Client Credentials Flow
- **Base URL**: `https://api.adp.com`
- **Token Endpoint**: `/auth/oauth/v2/token`
- **Grant Type**: `client_credentials`
- **Token Expiry**: Typically 1 hour
- **API Scopes**: Defined per integration

**Common Endpoints:**
- `/hr/v2/workers` - Employee/worker data
- `/payroll/v1/payroll-output` - Payroll information
- `/time/v2/time-cards` - Time tracking data
- `/talent/v1/performance-reviews` - Performance data

**Response Format:**
```json
{
  "workers": [...],
  "meta": {
    "total": 100,
    "offset": 0
  }
}
```

**Best Practices:**
- Cache access tokens (valid for 1 hour)
- Refresh tokens 5 minutes before expiry
- Use pagination for large datasets
- Implement webhook receivers for real-time updates
- Follow ADP's data retention policies

**Implementation Status**: ✅ **Implemented** in `/mcp-server/src/connectors/adp.py`

---

### 3. **DentalIntel API** ⚠️

**Documentation Status**: Partner/Customer-Only API

**Known Details:**
- **Type**: REST API (proprietary)
- **Authentication**: API Key-based
- **Data Types**: Practice analytics, benchmarking, patient insights
- **Access**: Requires DentalIntel partnership agreement

**Integration Approach:**
- Contact DentalIntel sales for API access
- Request developer documentation under NDA
- Typical endpoints include:
  - Analytics metrics
  - Benchmark comparisons
  - Patient retention data
  - Practice performance scores

**Next Steps:**
1. Contact DentalIntel: https://dentalintel.com/contact
2. Request API partnership
3. Obtain API credentials and documentation

**Implementation Status**: 🔶 **Stub Created** - Requires credentials

---

### 4. **Eaglesoft (Patterson Dental)** ⚠️

**Documentation Status**: HL7/Data Export Based

**Known Integration Methods:**
- **HL7 Interface**: Standard healthcare data format
- **Data Export**: CSV/XML file exports
- **Third-Party**: Patterson Technology Partner Program
- **Direct DB Access**: Via ODBC (read-only, requires license)

**Resources:**
- **Patterson Tech Partners**: https://www.pattersondental.com/technology-partners
- **HL7 Standard**: http://www.hl7.org/

**Integration Approaches:**
1. **File-Based** (Easiest):
   - Scheduled exports to SFTP/S3
   - Parse CSV/XML files
   - Import into data warehouse

2. **HL7 Interface**:
   - Real-time message passing
   - Requires HL7 interface license
   - Message types: ADT, SIU, ORM, ORU

3. **Database Access**:
   - Read-only ODBC connection
   - Requires Patterson approval
   - Query Eaglesoft SQL Server database

**Implementation Status**: 🔶 **File-Based Recommended** - API access limited

---

### 5. **Dentrix (Henry Schein)** ⚠️

**Documentation Status**: Dentrix Ascend API Available

**Resources:**
- **Dentrix Ascend**: Cloud-based platform with API
- **Classic Dentrix**: Database export or HL7 only
- **Henry Schein One**: https://www.henryscheinone.com

**Integration Methods:**

**Option A: Dentrix Ascend (Cloud)**
- REST API available for cloud version
- Requires Dentrix Ascend subscription
- Contact Henry Schein for API access

**Option B: Dentrix Classic (Desktop)**
- No direct API
- Database export via scheduled jobs
- HL7 messaging (ADT, SIU)
- Third-party integration tools

**Known Data Access:**
- Patient demographics
- Appointments and scheduling
- Treatment plans
- Insurance information
- Clinical notes

**Next Steps:**
1. Determine if practices use Ascend (cloud) or Classic (desktop)
2. For Ascend: Request API access from Henry Schein
3. For Classic: Implement file-based or HL7 integration

**Implementation Status**: 🔶 **Requires Assessment** - Version-dependent

---

## 🎯 **Implementation Priority**

Based on availability and documentation quality:

### **Tier 1: Ready to Implement** ✅
1. **NetSuite** - Full REST API, excellent docs, OAuth 1.0a
   - Status: ✅ Implemented
   - Confidence: High

2. **ADP** - Full REST API, good docs, OAuth 2.0
   - Status: ✅ Implemented
   - Confidence: High

### **Tier 2: Requires Credentials** 🔶
3. **DentalIntel** - REST API exists, need partnership
   - Action: Contact for API access
   - Timeline: 2-4 weeks

4. **Snowflake** - Data warehouse, well-documented
   - Action: Add snowflake-connector-python
   - Timeline: 1 week

### **Tier 3: Alternative Approaches** ⚠️
5. **Eaglesoft** - File-based or HL7
   - Recommendation: SFTP file exports
   - Timeline: 2-3 weeks

6. **Dentrix** - Version-dependent
   - Recommendation: Assess Classic vs Ascend
   - Timeline: Varies

---

## 🔑 **Authentication Summary**

| Integration | Auth Method | Token Type | Refresh | Complexity |
|-------------|-------------|------------|---------|------------|
| NetSuite | OAuth 1.0a TBA | Request signature | N/A | High |
| ADP | OAuth 2.0 | Bearer token | 1 hour | Medium |
| DentalIntel | API Key | Header | N/A | Low |
| Eaglesoft | File/HL7 | N/A | N/A | Low |
| Dentrix | Varies | Varies | Varies | Medium |
| Snowflake | User/Pass | Session | As needed | Medium |

---

## 🏗️ **Connector Implementation Pattern**

All connectors follow this reusable pattern (from `BaseConnector`):

```python
class MyConnector(BaseConnector):
    # 1. Properties
    @property
    def name(self) -> str:
        return "ServiceName"

    @property
    def integration_type(self) -> str:
        return "servicename"

    # 2. Authentication
    async def _get_auth_headers(self) -> Dict[str, str]:
        # Implement auth logic
        pass

    # 3. Connection Test
    async def _test_connection_impl(self):
        # Test API connectivity
        pass

    # 4. Data Fetching
    async def fetch_data(self, entity_type, filters):
        # Fetch from API
        pass

    # 5. Data Transformation
    async def transform_data(self, raw_data, entity_type):
        # Transform to standard format
        pass
```

**Built-in Features** (from `BaseConnector`):
- ✅ HTTP client with timeout
- ✅ Retry logic with exponential backoff
- ✅ Circuit breaker for fault tolerance
- ✅ Response caching
- ✅ Comprehensive logging
- ✅ Error handling

---

## 📖 **Additional Resources**

### NetSuite
- **Tutorials**: https://www.apideck.com/blog/integrating-with-the-netsuite-rest-api
- **Best Practices**: https://rollout.com/integration-guides/netsuite/api-essentials
- **Complete Guide**: https://nanonets.com/blog/netsuite-rest-api/

### ADP
- **Getting Started**: https://developers.adp.com/articles/guide/getting-started
- **Marketplace**: https://apps.adp.com/en-US/apps/

### General Integration Guides
- **OAuth 1.0a Spec**: https://tools.ietf.org/html/rfc5849
- **OAuth 2.0 Spec**: https://tools.ietf.org/html/rfc6749
- **HL7 FHIR**: https://www.hl7.org/fhir/

---

## 🔧 **Next Implementation Steps**

### 1. NetSuite Connector Enhancement
- [ ] Add SuiteQL support for complex queries
- [ ] Implement saved search execution
- [ ] Add batch operations
- [ ] Handle custom fields

### 2. ADP Connector Enhancement
- [ ] Add specific workforce endpoints
- [ ] Implement webhook handlers
- [ ] Add time & attendance APIs
- [ ] Support benefits data

### 3. Snowflake Integration
- [ ] Install `snowflake-connector-python`
- [ ] Implement connection pooling
- [ ] Create query templates
- [ ] Add result caching

### 4. DentalIntel Integration
- [ ] Obtain API credentials
- [ ] Review API documentation
- [ ] Implement connector
- [ ] Test with sandbox

### 5. Eaglesoft Integration
- [ ] Set up SFTP file export
- [ ] Create file parsers (CSV/XML)
- [ ] Schedule periodic imports
- [ ] Add data validation

### 6. Dentrix Integration
- [ ] Assess version (Classic vs Ascend)
- [ ] Choose integration method
- [ ] Implement accordingly

---

## 📞 **Vendor Contact Information**

### API Access Requests:
- **NetSuite**: Via Oracle account manager or partner
- **ADP**: https://developers.adp.com/contact
- **DentalIntel**: https://dentalintel.com/contact
- **Patterson (Eaglesoft)**: https://www.pattersondental.com/support
- **Henry Schein (Dentrix)**: https://www.henryschein.com/contact

### Support:
- **NetSuite**: NetSuite Help Center
- **ADP**: Developer forum at developers.adp.com
- **Others**: Contact via sales/support channels

---

**Last Updated**: October 26, 2025
**Maintainer**: MCP Server Development Team
**Status**: Living Document - Update as APIs evolve
