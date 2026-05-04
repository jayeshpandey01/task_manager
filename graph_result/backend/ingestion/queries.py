# Cypher queries for creating the O2C Graph Schema

CREATE_CONSTRAINTS = [
    "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (o:SalesOrder) REQUIRE o.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (oi:SalesOrderItem) REQUIRE oi.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (d:OutboundDelivery) REQUIRE d.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (di:OutboundDeliveryItem) REQUIRE di.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (b:BillingDocument) REQUIRE b.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (bi:BillingDocumentItem) REQUIRE bi.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (a:AccountingDocument) REQUIRE a.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (pl:Plant) REQUIRE pl.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (sl:StorageLocation) REQUIRE sl.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (ad:Address) REQUIRE ad.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (sl:ScheduleLine) REQUIRE sl.id IS UNIQUE"
]

CREATE_VECTOR_INDEXES = [
    "CREATE VECTOR INDEX product_description_vector IF NOT EXISTS FOR (p:Product) ON (p.embedding) OPTIONS {indexConfig: {`vector.dimensions`: 768, `vector.similarity_function`: 'cosine'}}",
    "CREATE VECTOR INDEX customer_name_vector IF NOT EXISTS FOR (c:Customer) ON (c.embedding) OPTIONS {indexConfig: {`vector.dimensions`: 768, `vector.similarity_function`: 'cosine'}}",
    "CREATE VECTOR INDEX customer_category_vector IF NOT EXISTS FOR (c:Customer) ON (c.category_embedding) OPTIONS {indexConfig: {`vector.dimensions`: 768, `vector.similarity_function`: 'cosine'}}"
]

MERGE_CUSTOMER = """
UNWIND $batch AS row
MERGE (c:Customer {id: row.businessPartner})
SET c.name = row.businessPartnerFullName,
    c.category = row.businessPartnerCategory,
    c.creationDate = row.creationDate,
    c.isBlocked = row.businessPartnerIsBlocked
"""

MERGE_ADDRESS = """
UNWIND $batch AS row
// Extract address from business partner address data
MERGE (a:Address {id: row.addressId})
SET a.cityName = row.cityName,
    a.streetName = row.streetName,
    a.country = row.country,
    a.postalCode = row.postalCode,
    a.houseNumber = row.houseNumber

WITH a, row
WHERE row.businessPartner IS NOT NULL AND row.businessPartner <> ""
MERGE (c:Customer {id: row.businessPartner})
MERGE (c)-[:HAS_ADDRESS]->(a)
"""

MERGE_PRODUCT = """
UNWIND $batch AS row
MERGE (p:Product {id: row.product})
SET p.type = row.productType,
    p.group = row.productGroup,
    p.baseUnit = row.baseUnit,
    p.netWeight = row.netWeight,
    p.creationDate = row.creationDate
"""

MERGE_PRODUCT_DESCRIPTION = """
UNWIND $batch AS row
MATCH (p:Product {id: row.product})
SET p.description = row.productDescription
"""

MERGE_PLANT = """
UNWIND $batch AS row
MERGE (pl:Plant {id: row.plant})
SET pl.name = row.plantName,
    pl.salesOrganization = row.salesOrganization

WITH pl, row
WHERE row.addressId IS NOT NULL AND row.addressId <> ""
MERGE (a:Address {id: row.addressId})
MERGE (pl)-[:HAS_ADDRESS]->(a)
"""

MERGE_PRODUCT_PLANT = """
UNWIND $batch AS row
MATCH (p:Product {id: row.product})
MERGE (pl:Plant {id: row.plant})
MERGE (p)-[:PRODUCED_AT]->(pl)
SET pl.profitCenter = row.profitCenter,
    pl.mrpType = row.mrpType
"""

MERGE_PRODUCT_STORAGE_LOCATION = """
UNWIND $batch AS row
MATCH (p:Product {id: row.product})
MERGE (pl:Plant {id: row.plant})
MERGE (sl:StorageLocation {id: row.plant + '_' + row.storageLocation})
SET sl.code = row.storageLocation,
    sl.plantId = row.plant
MERGE (pl)-[:HAS_STORAGE_LOCATION]->(sl)
MERGE (p)-[:STORED_IN]->(sl)
"""

MERGE_SALES_ORDER = """
UNWIND $batch AS row
MERGE (o:SalesOrder {id: row.salesOrder})
SET o.creationDate = row.creationDate,
    o.totalNetAmount = row.totalNetAmount,
    o.transactionCurrency = row.transactionCurrency,
    o.overallDeliveryStatus = row.overallDeliveryStatus,
    o.salesOrderType = row.salesOrderType
MERGE (c:Customer {id: row.soldToParty})
MERGE (c)-[:PLACED]->(o)
"""

MERGE_SALES_ORDER_ITEM = """
UNWIND $batch AS row
MERGE (oi:SalesOrderItem {id: row.salesOrder + '_' + row.salesOrderItem})
SET oi.salesOrder = row.salesOrder,
    oi.itemNumber = row.salesOrderItem,
    oi.material = row.material,
    oi.requestedQuantity = row.requestedQuantity,
    oi.netAmount = row.netAmount,
    oi.currency = row.transactionCurrency,
    oi.plant = row.productionPlant,
    oi.storageLocation = row.storageLocation

MERGE (o:SalesOrder {id: row.salesOrder})
MERGE (o)-[:HAS_ITEM]->(oi)

WITH oi, row
WHERE row.material IS NOT NULL AND row.material <> ""
MERGE (p:Product {id: row.material})
MERGE (oi)-[:IS_PRODUCT]->(p)

WITH oi, row
WHERE row.productionPlant IS NOT NULL AND row.productionPlant <> ""
MERGE (pl:Plant {id: row.productionPlant})
MERGE (oi)-[:SHIPPED_FROM]->(pl)

WITH oi, row
WHERE row.storageLocation IS NOT NULL AND row.storageLocation <> ""
MERGE (sl:StorageLocation {id: row.productionPlant + '_' + row.storageLocation})
MERGE (oi)-[:STORED_IN]->(sl)
"""

MERGE_SALES_ORDER_SCHEDULE_LINE = """
UNWIND $batch AS row
MERGE (sl:ScheduleLine {id: row.salesOrder + '_' + row.salesOrderItem + '_' + row.scheduleLine})
SET sl.salesOrder = row.salesOrder,
    sl.salesOrderItem = row.salesOrderItem,
    sl.scheduleLineNumber = row.scheduleLine,
    sl.confirmedDeliveryDate = row.confirmedDeliveryDate,
    sl.confirmedQuantity = row.confdOrderQtyByMatlAvailCheck,
    sl.unit = row.orderQuantityUnit

MERGE (oi:SalesOrderItem {id: row.salesOrder + '_' + row.salesOrderItem})
MERGE (oi)-[:HAS_SCHEDULE_LINE]->(sl)
"""

MERGE_OUTBOUND_DELIVERY = """
UNWIND $batch AS row
MERGE (d:OutboundDelivery {id: row.deliveryDocument})
SET d.creationDate = row.creationDate,
    d.overallGoodsMovementStatus = row.overallGoodsMovementStatus,
    d.overallPickingStatus = row.overallPickingStatus,
    d.shippingPoint = row.shippingPoint,
    d.actualGoodsMovementDate = row.actualGoodsMovementDate
"""

MERGE_OUTBOUND_DELIVERY_ITEM = """
UNWIND $batch AS row
MERGE (di:OutboundDeliveryItem {id: row.deliveryDocument + '_' + row.deliveryDocumentItem})
SET di.deliveryDocument = row.deliveryDocument,
    di.itemNumber = row.deliveryDocumentItem,
    di.actualDeliveryQuantity = row.actualDeliveryQuantity,
    di.deliveryQuantityUnit = row.deliveryQuantityUnit,
    di.plant = row.plant,
    di.storageLocation = row.storageLocation

MERGE (d:OutboundDelivery {id: row.deliveryDocument})
MERGE (d)-[:HAS_ITEM]->(di)

WITH di, row
WHERE row.plant IS NOT NULL AND row.plant <> ""
MERGE (pl:Plant {id: row.plant})
MERGE (di)-[:SHIPPED_FROM]->(pl)

WITH di, row
WHERE row.storageLocation IS NOT NULL AND row.storageLocation <> ""
MERGE (sl:StorageLocation {id: row.plant + '_' + row.storageLocation})
MERGE (di)-[:STORED_IN]->(sl)

WITH di, row
WHERE row.referenceSdDocument IS NOT NULL AND row.referenceSdDocument <> ""
// Link back to the sales order item
MERGE (oi:SalesOrderItem {id: row.referenceSdDocument + '_' + row.referenceSdDocumentItem})
MERGE (di)-[:FULFILLS]->(oi)
"""

MERGE_BILLING_DOCUMENT = """
UNWIND $batch AS row
MERGE (b:BillingDocument {id: row.billingDocument})
SET b.billingDocumentDate = row.billingDocumentDate,
    b.totalNetAmount = row.totalNetAmount,
    b.transactionCurrency = row.transactionCurrency,
    b.isCancelled = row.billingDocumentIsCancelled,
    b.billingDocumentType = row.billingDocumentType

WITH b, row
WHERE row.soldToParty IS NOT NULL AND row.soldToParty <> ""
MERGE (c:Customer {id: row.soldToParty})
MERGE (b)-[:BILLED_TO]->(c)

WITH b, row
WHERE row.accountingDocument IS NOT NULL AND row.accountingDocument <> "" AND row.accountingDocument <> "0000000000"
MERGE (a:AccountingDocument {id: row.accountingDocument})
MERGE (b)-[:HAS_ACCOUNTING_DOC]->(a)
"""

MERGE_BILLING_DOCUMENT_ITEM = """
UNWIND $batch AS row
MERGE (bi:BillingDocumentItem {id: row.billingDocument + '_' + row.billingDocumentItem})
SET bi.billingDocument = row.billingDocument,
    bi.itemNumber = row.billingDocumentItem,
    bi.material = row.material,
    bi.billingQuantity = row.billingQuantity,
    bi.netAmount = row.netAmount

MERGE (b:BillingDocument {id: row.billingDocument})
MERGE (b)-[:HAS_ITEM]->(bi)

WITH bi, row
WHERE row.referenceSdDocument IS NOT NULL AND row.referenceSdDocument <> ""
// Can link to outbound delivery item OR sales order item based on document type. Usually OutboundDelivery for delivery-related billing.
// We'll link to both using MATCH to see if it exists. But to be safe in a schema, we can link directly to OutboundDeliveryItem 
// since standard O2C is Order -> Delivery -> Billing (unless order-related billing). Let's create a generic reference node.
MERGE (refItem {id: row.referenceSdDocument + '_' + row.referenceSdDocumentItem})
MERGE (bi)-[:BILLS_FOR]->(refItem)
"""

MERGE_PAYMENT = """
UNWIND $batch AS row
MERGE (a:AccountingDocument {id: row.accountingDocument})
SET a.companyCode = row.companyCode,
    a.fiscalYear = row.fiscalYear,
    a.clearingDate = row.clearingDate,
    a.amountInTransactionCurrency = row.amountInTransactionCurrency,
    a.transactionCurrency = row.transactionCurrency,
    a.postingDate = row.postingDate,
    a.documentDate = row.documentDate

WITH a, row
WHERE row.customer IS NOT NULL AND row.customer <> ""
MERGE (c:Customer {id: row.customer})
MERGE (c)-[:PAID]->(a)
"""

# Vector Embedding Queries
UPDATE_PRODUCT_EMBEDDING = """
UNWIND $batch AS row
MATCH (p:Product {id: row.id})
CALL db.create.setNodeVectorProperty(p, 'embedding', row.embedding)
"""

UPDATE_CUSTOMER_EMBEDDING = """
UNWIND $batch AS row
MATCH (c:Customer {id: row.id})
CALL db.create.setNodeVectorProperty(c, 'embedding', row.embedding)
"""

UPDATE_CUSTOMER_CATEGORY_EMBEDDING = """
UNWIND $batch AS row
MATCH (c:Customer {id: row.id})
CALL db.create.setNodeVectorProperty(c, 'category_embedding', row.embedding)
"""

VECTOR_QUERY_PRODUCT = """
CALL db.index.vector.queryNodes('product_description_vector', 5, $query_vector)
YIELD node, score
RETURN node.id as id, node.description as description, score
"""

VECTOR_QUERY_CUSTOMER = """
CALL db.index.vector.queryNodes('customer_name_vector', 5, $query_vector)
YIELD node, score
RETURN node.id as id, node.name as name, score
"""
