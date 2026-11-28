"use strict";

const words = {
  brand: ["راي للذكاء العقاري", "RAI Property Intelligence"], subbrand: ["سلطنة عُمان", "Sultanate of Oman"],
  directory: ["دليل العقارات", "Property directory"], market: ["مؤشرات السوق", "Market intelligence"], sources: ["المصادر", "Data sources"],
  directoryTitle: ["دليل العقارات في عُمان", "Property directory for Oman"],
  directoryLead: ["ابحث في الإعلانات المتاحة للنشر وتتبّع أسعار العرض ومصادرها.", "Explore publishable listings, advertised prices and their sources."],
  marketTitle: ["مرصد السوق العقاري", "Oman real estate observatory"],
  marketLead: ["تابع بيانات الإعلانات المرصودة والإحصاءات العقارية الرسمية.", "Track observed listings and official real estate statistics."],
  sourcesTitle: ["مصادر البيانات", "Data coverage and attribution"],
  sourcesLead: ["اطّلع على منشأ البيانات والتغطية وشروط الاستخدام.", "See the origin, coverage and terms of the data."],
  coverage: ["محافظة ضمن الدليل الجغرافي", "governorates in the geographic directory"],
  filters: ["تصفية النتائج", "Filters"], reset: ["مسح", "Clear"], all: ["الكل", "All"],
  cards: ["بطاقات", "Cards"], list: ["قائمة", "List"], map: ["خريطة", "Map"], sort: ["ترتيب", "Sort"],
  newest: ["آخر رصد", "Latest observed"], lowest: ["الأقل سعراً", "Price low to high"], highest: ["الأعلى سعراً", "Price high to low"],
  gov: ["المحافظة", "Governorate"], wilaya: ["الولاية", "Wilayat"], area: ["المنطقة", "Area"],
  kind: ["نوع العقار", "Property type"], deal: ["نوع العرض", "Offer type"], source: ["المصدر", "Source"],
  minPrice: ["من سعر (ر.ع.)", "Min price (OMR)"], maxPrice: ["إلى سعر (ر.ع.)", "Max price (OMR)"],
  minLand: ["مساحة أرض من", "Min land m²"], maxLand: ["مساحة أرض إلى", "Max land m²"],
  minBuilt: ["مساحة بناء من", "Min built m²"], maxBuilt: ["مساحة بناء إلى", "Max built m²"],
  publishedFrom: ["النشر من", "Published from"], publishedTo: ["النشر إلى", "Published through"],
  periodFrom: ["الرصد من", "Observed from"], periodTo: ["الرصد إلى", "Observed through"],
  freshness: ["حداثة الرصد", "Freshness"], recent: ["رصد حديث", "Recently observed"], older: ["رصد قديم", "Older observation"],
  firstRecent: ["رُصد لأول مرة مؤخراً", "First observed recently"],
  noDate: ["تاريخ النشر غير متاح", "Publication date unknown"], recentlyVerified: ["تحقق حديث", "Recently verified"],
  verification: ["التحقق", "Verification"], quality: ["جودة البيانات", "Data quality"],
  flagged: ["عليه ملاحظات", "Flagged"], clear: ["بلا ملاحظات", "No flags"], results: ["إعلان", "listings"],
  noListings: ["الإعلانات غير متاحة للنشر حالياً", "No listings are currently available for publication"],
  noListingsText: ["يمكنك تصفح التقسيم الجغرافي والإحصاءات العقارية الرسمية.", "You can explore the geographic directory and official real estate statistics."],
  noMatches: ["لا توجد نتائج مطابقة", "No matching listings"], adjust: ["عدّل عوامل التصفية لتوسيع البحث.", "Adjust the filters to broaden the search."],
  details: ["التفاصيل", "Details"], original: ["فتح المصدر", "Open source"], compare: ["مقارنة", "Compare"],
  remove: ["إزالة", "Remove"], close: ["إغلاق", "Close"], price: ["السعر", "Price"], availability: ["التوفر", "Availability"],
  priceBasis: ["أساس السعر", "Price basis"], verifiedAt: ["آخر تحقق", "Last verified"], seen: ["آخر رصد", "Last observed"],
  published: ["تاريخ النشر", "Published"], bedrooms: ["غرف النوم", "Bedrooms"], land: ["مساحة الأرض", "Land area"],
  built: ["مساحة البناء", "Built-up area"], sqm: ["سعر المتر المربع", "Price per m²"], approx: ["موقع تقريبي", "Approximate location"],
  noCoordinates: ["الموقع على الخريطة غير متاح", "Map location unavailable"],
  dup: ["تكرار محتمل", "Duplicate candidates"], history: ["تاريخ تغيّر السعر", "Price change history"],
  noHistory: ["لا توجد قراءات سعرية مؤرخة متاحة.", "No dated price readings are available."],
  verifyNotice: ["تحقق من حالة الإعلان لدى المصدر قبل اتخاذ قرار.", "Check the listing’s status with the source before making a decision."],
  nearby: ["الخدمات القريبة", "Nearby services"], straight: ["المسافات بخط مستقيم من موقع تقريبي؛ تتفاوت تغطية الخدمات.", "Straight-line distances from an approximate location. Service coverage varies."],
  km: ["كم", "km"], mapFail: ["تعذر تحميل الخريطة.", "The map could not be loaded."],
  mapNoPins: ["لا توجد إحداثيات عقارات قابلة للعرض ضمن هذا الاختيار.", "No publishable listing coordinates match this selection."],
  official: ["إحصاءات السوق الرسمية", "Official market statistics"], method: [
    "قراءات الإعلانات تعكس العينة المرصودة. قد تتغير النتائج بسبب اختلاف تغطية المصادر وفترات الرصد.",
    "Listing measures describe the observed sample. Changes can reflect source coverage and observation periods."],
  officialNote: ["تُنسب الأرقام إلى المركز الوطني للإحصاء والمعلومات ووزارة الإسكان والتخطيط العمراني. أعداد صفوف الوزارة تصف ملفات البيانات المفتوحة.",
    "Figures are attributed to NCSI and the Ministry of Housing and Urban Planning. Ministry row counts describe open-data files."],
  observations: ["قراءات الإعلانات", "Listing observations"], distinct: ["سجلات إعلانات مميزة", "Distinct listing records"],
  unique: ["تقدير العقارات المميزة", "Estimated unique properties"], duplicateRate: ["سجلات لها مرشح تكرار", "Listings with duplicate candidates"],
  complete: ["اكتمال الحقول الأساسية", "Core field completeness"], duration: ["وسيط مدة الرصد بالأيام", "Median observed duration (days)"],
  marketEmpty: ["لا توجد إعلانات متاحة ضمن عوامل التصفية الحالية.", "No publishable listings match these filters."],
  estimateNote: ["تُحسب المجموعة المؤكدة بالمراجعة اليدوية مرة واحدة، ويُحسب كل سجل غير مرتبط مرة واحدة. قد يبقى تكرار غير محسوم.",
    "A manually confirmed group counts once. Each unlinked record counts once. Unresolved duplication may remain."],
  distribution: ["توزيع العينة", "Sample distribution"], priceTrends: ["اتجاهات أسعار العرض", "Advertised price trends"],
  currentPrices: ["توزيع أسعار العرض", "Advertised price distribution"], newListings: ["أول رصد علني", "First public observation"],
  month: ["الفترة", "Period"], changes: ["تغيّرات السعر", "Price changes"], n: ["العدد", "Count"], median: ["الوسيط", "Median"],
  min: ["الأدنى", "Minimum"], max: ["الأعلى", "Maximum"], indicator: ["المؤشر", "Indicator"], value: ["القيمة", "Value"],
  chartMetric: ["المؤشر في الرسم", "Chart metric"], noOfficial: ["لا توجد إحصاءات رسمية لهذا الاختيار.", "No official figures match this selection."],
  officialSource: ["مصدر الإحصاء", "Statistical source"], country: ["سلطنة عُمان", "Oman"],
  allG: ["التغطية", "Coverage"], license: ["شروط المصدر", "Source terms"], updated: ["آخر تصدير للبيانات", "Data snapshot exported"],
  fail: ["تعذر تحميل البيانات. أعد تحميل الصفحة.", "Data could not be loaded. Reload the page to retry."],
  loading: ["جارٍ تحميل البيانات…", "Loading data…"], mapIssue: ["الإبلاغ عن مشكلة في الخريطة", "Report a map issue"],
  propertiesLayer: ["العقارات", "Properties"], age: ["عدد أيام الرصد", "Observed days"],
  status_unknown: ["الحالة غير معروفة", "Status unknown"], status_available: ["متاح وفق المصدر", "Available per source"],
  status_unreachable: ["تعذر الوصول", "Unreachable"], status_withdrawn: ["أزيل من المصدر", "Withdrawn"],
  status_sold_confirmed: ["بيع مؤكد", "Sale independently confirmed"], status_let_confirmed: ["تأجير مؤكد", "Let independently confirmed"],
  verify_unverified: ["غير متحقق", "Unverified"], verify_source_checked: ["تم فحص المصدر", "Source checked"],
  verify_advertiser_confirmed: ["تأكيد المعلن", "Advertiser confirmed"], verify_independently_verified: ["تحقق مستقل", "Independently verified"],
  basis_advertised: ["سعر العرض", "Advertised price"], basis_advertiser_confirmed: ["السعر المؤكد من المعلن", "Advertiser-confirmed price"],
  basis_independently_verified: ["سعر تحقق منه طرف مستقل", "Independently verified price"], basis_transaction: ["سعر المعاملة", "Transaction price"],
  kind_villa: ["فيلا", "Villa"], kind_house: ["منزل", "House"], kind_apartment: ["شقة", "Apartment"], kind_farm: ["مزرعة", "Farm"],
  kind_commercial: ["عقار تجاري", "Commercial property"], "kind_residential-land": ["أرض سكنية", "Residential land"],
  "kind_commercial-land": ["أرض تجارية", "Commercial land"], "kind_industrial-land": ["أرض صناعية", "Industrial land"],
  "kind_mixed-land": ["أرض سكنية تجارية", "Mixed-use land"], kind_chalet: ["شاليه", "Chalet"],
  deal_sale: ["بيع", "Sale"], deal_rent: ["إيجار", "Rent"], period_day: ["يومي", "Daily"], period_week: ["أسبوعي", "Weekly"],
  period_month: ["شهري", "Monthly"], period_year: ["سنوي", "Yearly"], unit_million_omr: ["مليون ر.ع.", "million OMR"],
  unit_count: ["عدد", "count"], unit_rows: ["صف", "rows"], point_mosque: ["مساجد", "Mosques"], point_school: ["مدارس", "Schools"],
  point_health: ["صحة", "Health services"], point_shop: ["تسوّق", "Shopping"], point_park: ["حدائق", "Parks"],
  point_road: ["طرق", "Roads"], point_public: ["خدمات عامة", "Public services"],
  stat_traded_property_value: ["القيمة المتداولة للعقار", "Traded value of property"],
  stat_sales_contract_value: ["القيمة المتداولة لعقود البيع", "Traded value of sales contracts"],
  stat_sales_contract_count: ["عدد عقود البيع", "Sales contracts"],
  stat_properties_issued_count: ["الملكيات الصادرة", "Properties issued"],
  stat_published_dataset_rows: ["صفوف بيانات البيع والشراء المنشورة", "Published buy/sell dataset rows"],
  flag_unknown_publication_date: ["تاريخ النشر غير معروف", "Publication date unknown"],
  flag_verification_required: ["يتطلب التحقق", "Verification required"],
  flag_missing_area: ["المنطقة غير مذكورة", "Local area missing"],
  flag_missing_wilayat: ["الولاية غير مذكورة", "Wilayat missing"], flag_unknown_wilayat: ["تعذر توحيد اسم الولاية", "Wilayat name unmatched"],
  flag_missing_governorate: ["المحافظة غير مذكورة", "Governorate missing"], flag_unknown_governorate: ["تعذر توحيد اسم المحافظة", "Governorate name unmatched"],
  flag_missing_price: ["السعر غير مذكور", "Price missing"], flag_invalid_price: ["قيمة السعر غير صالحة", "Invalid price"],
  flag_missing_kind: ["نوع العقار غير مذكور", "Property type missing"], flag_invalid_kind: ["نوع العقار غير معروف", "Property type unmatched"],
  flag_missing_deal: ["نوع العرض غير مذكور", "Offer type missing"], flag_invalid_deal: ["نوع العرض غير معروف", "Offer type unmatched"],
  flag_missing_currency: ["عملة السعر غير مذكورة", "Currency missing"], flag_invalid_currency: ["عملة السعر غير معروفة", "Unrecognized currency"],
  flag_missing_rental_period: ["دورية الإيجار غير مذكورة", "Rental period missing"], flag_invalid_rental_period: ["دورية الإيجار غير صالحة", "Invalid rental period"],
  flag_invalid_land_m2: ["مساحة الأرض غير صالحة", "Invalid land area"], flag_invalid_built_m2: ["مساحة البناء غير صالحة", "Invalid built-up area"],
  flag_invalid_bedrooms: ["عدد الغرف غير صالح", "Invalid bedroom count"], flag_invalid_coordinates: ["الإحداثيات غير صالحة", "Invalid coordinates"],
  flag_invalid_publication_date: ["تاريخ النشر غير صالح", "Invalid publication date"], flag_invalid_verification_date: ["تاريخ التحقق غير صالح", "Invalid verification date"],
  flag_missing_dimensions: ["المساحات غير متاحة", "Dimensions unavailable"], flag_geographic_conflict: ["تعارض جغرافي", "Geographic mismatch"],
  flag_unsubstantiated_status: ["حالة التوفر غير موثقة", "Availability status unsupported"], flag_unsubstantiated_price_basis: ["أساس السعر غير موثق", "Price basis unsupported"],
  flag_large_price_change: ["تغيّر سعري كبير", "Large advertised price change"],
  flag_comparable_price_outlier: ["السعر بعيد عن أسعار العقارات المماثلة", "Price differs from comparable listings"],
  flag_comparable_sqm_outlier: ["سعر المتر بعيد عن أسعار العقارات المماثلة", "Unit price differs from comparable listings"],
  flag_changed_currency_or_period: ["تغيرت العملة أو الدورية", "Currency or period changed"],
  flag_conflicting_source_record: ["سجلان متعارضان للمصدر", "Conflicting source records"],
};

const MAIN_VIEWS = ["directory", "market", "sources"];
const PROPERTY_TYPES = ["residential-land", "commercial-land", "mixed-land", "industrial-land", "villa", "house", "apartment", "commercial", "farm", "chalet"];
const STAT_INDICATORS = ["traded_property_value", "sales_contract_value", "sales_contract_count", "properties_issued_count", "published_dataset_rows"];
const LAYERS = ["propertiesLayer", "mosque", "school", "health", "shop", "park", "road", "public"];
const state = { lang: "ar", view: "cards", filters: {}, market: {}, official: {}, compare: new Set(), layers: new Set(["propertiesLayer"]), data: null };

const $ = (id) => document.getElementById(id);
const t = (key) => words[key]?.[state.lang === "ar" ? 0 : 1] ?? key;
const fmt = (value, decimals = 2) => value === null || value === undefined ? "—" : new Intl.NumberFormat(state.lang === "ar" ? "ar-OM" : "en-OM", {maximumFractionDigits: decimals}).format(value);
const day = (value) => value?.slice(0, 10) ?? "—";
const el = (name, content, className) => {
  const node = document.createElement(name);
  if (content !== undefined && content !== null) node.textContent = content;
  if (className) node.className = className;
  return node;
};
const localizedPairs = (values, prefix) => values.map((v) => [v, t(prefix + v)]);
const formatPrice = (row) => row.price === null ? "—" : [fmt(Number(row.price), 3), row.currency, row.rental_period && t("period_" + row.rental_period)].filter(Boolean).join(" · ");

function link(url, label) {
  let validated;
  try { validated = new URL(url); } catch { return el("span", label); }
  if (validated.protocol !== "https:" || validated.username || validated.password) return el("span", label);
  const anchor = el("a", label);
  anchor.href = validated.href;
  anchor.target = "_blank";
  anchor.rel = "noopener noreferrer";
  return anchor;
}

function button(label, handler) {
  const node = el("button", label);
  node.type = "button";
  node.addEventListener("click", handler);
  return node;
}

function selectOptions(select, pairs, selected, blank = true) {
  select.replaceChildren();
  if (blank) select.add(new Option(t("all"), ""));
  pairs.forEach(([value, label]) => select.add(new Option(label, value)));
  select.value = selected ?? "";
  if (select.selectedIndex < 0 && select.options.length) select.selectedIndex = 0;
}

function field(key, form, render, type, pairs) {
  const label = el("label", null, "field");
  const input = el(type === "select" ? "select" : "input");
  input.name = key;
  if (type === "select") {
    selectOptions(input, pairs, form[key]);
  } else {
    input.type = type;
    if (type === "number") {
      input.min = "0";
      input.step = "any";
    }
    input.value = form[key] ?? "";
  }
  input.addEventListener("change", () => { form[key] = input.value; render(key); });
  label.append(el("span", t(key)), input);
  return label;
}

function areaOptions() {
  const selected = state.filters;
  return [...new Map(state.data.listings.filter((row) => row.area_key && (!selected.gov || selected.gov === row.governorate) &&
    (!selected.wilaya || selected.wilaya === row.wilayat)).map((row) => [row.area_key, row.area])).entries()];
}

function locationOptions(governor) {
  return state.data.geography.governorates.filter(([id]) => !governor || id === governor).flatMap(([id, ar, en, children]) =>
    children.map(([wilaya, nameAr, nameEn]) => [wilaya, state.lang === "ar" ? nameAr : nameEn]));
}

function governorOptions() {
  return state.data.geography.governorates.map(([id, ar, en]) => [id, state.lang === "ar" ? ar : en]);
}

function makeFilters() {
  const listingFields = (key) => {
    if (key === "gov") { state.filters.wilaya = ""; state.filters.area = ""; }
    if (key === "wilaya") state.filters.area = "";
    if (key === "gov" || key === "wilaya") makeFilters();
    renderDirectory();
  };
  const marketFields = (key) => {
    if (key === "gov") { state.market.wilaya = ""; makeFilters(); }
    renderMarket();
  };
  const dir = (key, pairs = []) => field(key, state.filters, listingFields, "select", pairs);
  const mkt = (key, pairs) => field(key, state.market, marketFields, "select", pairs);
  const pair = (first, second, type) => {
    const container = el("div", null, "pair");
    for (const key of [first, second]) container.append(field(key, state.filters, listingFields, type));
    return container;
  };
  const types = localizedPairs(PROPERTY_TYPES, "kind_");
  $("directoryFilters").replaceChildren(
    dir("gov", governorOptions()), dir("wilaya", locationOptions(state.filters.gov)), dir("area", areaOptions()), dir("kind", types),
    dir("deal", localizedPairs(["sale", "rent"], "deal_")),
    pair("minPrice", "maxPrice", "number"), pair("minLand", "maxLand", "number"), pair("minBuilt", "maxBuilt", "number"),
    dir("source", Object.entries(state.data.sources).filter(([, s]) => s.categories.includes("listings")).map(([id, s]) => [id, s.name])),
    pair("publishedFrom", "publishedTo", "date"), dir("freshness", localizedPairs(["firstRecent", "recent", "older", "recentlyVerified", "noDate"], "")),
    dir("verification", localizedPairs(["unverified", "source_checked", "advertiser_confirmed", "independently_verified"], "verify_")),
    dir("quality", localizedPairs(["flagged", "clear"], "")),
  );
  $("marketFilters").replaceChildren(mkt("gov", governorOptions()), mkt("wilaya", locationOptions(state.market.gov)), mkt("kind", types),
    field("periodFrom", state.market, marketFields, "month"), field("periodTo", state.market, marketFields, "month"));
  selectOptions($("sort"), localizedPairs(["newest", "lowest", "highest"], ""), state.filters.sort ?? "newest", false);
}

function within(value, low, high) {
  return (!low && !high) || (value !== null && (!low || Number(value) >= Number(low)) && (!high || Number(value) <= Number(high)));
}

function freshness(row, fieldName) {
  const age = (value) => value ? (Date.now() - Date.parse(value)) / 86400000 : Infinity;
  const threshold = state.data.fresh_days;
  switch (fieldName) {
    case "firstRecent": return age(row.first_observed) <= threshold;
    case "recent": return age(row.last_observed) <= threshold;
    case "older": return row.last_observed && age(row.last_observed) > threshold;
    case "recentlyVerified": return age(row.last_verified) <= threshold;
    case "noDate": return !row.published_at;
    default: return true;
  }
}

function matches(row, f) {
  const pairs = [["gov", "governorate"], ["wilaya", "wilayat"], ["area", "area_key"], ["kind", "kind"],
    ["deal", "deal"], ["source", "source_id"], ["verification", "verification"]];
  return pairs.every(([key, name]) => !f[key] || f[key] === row[name]) &&
    within(row.currency === "OMR" ? row.price : null, f.minPrice, f.maxPrice) &&
    within(row.land_m2, f.minLand, f.maxLand) && within(row.built_m2, f.minBuilt, f.maxBuilt) &&
    (!f.publishedFrom || row.published_at?.slice(0, 10) >= f.publishedFrom) &&
    (!f.publishedTo || row.published_at?.slice(0, 10) <= f.publishedTo) &&
    freshness(row, f.freshness) && (!f.quality || (f.quality === "flagged") === Boolean(row.quality_flags.length));
}

function locationLabel(row) {
  const name = (pair) => pair?.[1] ?? "—";
  return [row.area, row.wilayat && name(locationOptions(row.governorate).find(([id]) => id === row.wilayat)),
    row.governorate && name(governorOptions().find(([id]) => id === row.governorate))].filter(Boolean).join(" · ") || "—";
}

function listingTitle(row) {
  return [row.kind && t("kind_" + row.kind), row.deal && t("deal_" + row.deal)].filter(Boolean).join(" · ") || t("details");
}

function empty(title, description, cta) {
  const node = el("div", null, "empty");
  node.append(el("h2", t(title)), el("p", t(description), "muted"));
  if (cta) {
    const anchor = el("a", t("market"));
    anchor.href = "#market";
    node.append(anchor);
  }
  return node;
}

function listingCard(row) {
  const article = el("article", null, "result");
  const body = el("div");
  body.append(el("h3", listingTitle(row)), el("p", locationLabel(row), "muted"), el("strong", formatPrice(row)));
  const meta = el("div", null, "actions");
  meta.append(el("span", t("status_" + row.availability), "chip"));
  if (row.duplicate_candidates) meta.append(el("span", t("dup"), "chip"));
  body.append(meta);
  const actions = el("div", null, "actions");
  actions.append(button(t("details"), () => details(row)), button(t(state.compare.has(row.listing_id) ? "remove" : "compare"), () => {
    if (state.compare.has(row.listing_id)) state.compare.delete(row.listing_id);
    else if (state.compare.size < 4) state.compare.add(row.listing_id);
    renderDirectory();
  }));
  article.append(body, actions);
  return article;
}

function table(headers, rows) {
  const wrapper = el("div", null, "table-wrap");
  const grid = el("table");
  const thead = el("thead");
  const header = el("tr");
  for (const name of headers) {
    const cell = el("th", name);
    cell.scope = "col";
    header.append(cell);
  }
  thead.append(header);
  const tbody = el("tbody");
  for (const values of rows) {
    const row = el("tr");
    for (const value of values) {
      const cell = el("td");
      if (value instanceof Node) cell.append(value);
      else cell.textContent = value ?? "—";
      row.append(cell);
    }
    tbody.append(row);
  }
  grid.append(thead, tbody);
  wrapper.append(grid);
  return wrapper;
}

function popup(title, content) {
  $("dialogTitle").textContent = title;
  $("dialogBody").replaceChildren(content);
  if (!$("dialog").open) $("dialog").showModal();
}

function details(row) {
  const content = el("div");
  content.append(el("p", t("verifyNotice"), "notice"), table([t("indicator"), t("value")], [
    [t("area"), locationLabel(row)], [t("price"), formatPrice(row)], [t("priceBasis"), t("basis_" + row.price_basis)],
    [t("availability"), t("status_" + row.availability)], [t("verification"), t("verify_" + row.verification)],
    [t("verifiedAt"), day(row.last_verified)], [t("seen"), day(row.last_observed)], [t("published"), day(row.published_at)],
    [t("land"), fmt(row.land_m2)], [t("built"), fmt(row.built_m2)], [t("bedrooms"), fmt(row.bedrooms, 0)], [t("sqm"), fmt(row.price_per_m2)],
    [t("map"), t(row.accuracy === "approximate" ? "approx" : "noCoordinates")], [t("dup"), fmt(row.duplicate_candidates, 0)],
    [t("quality"), row.quality_flags.map((flag) => t("flag_" + flag)).join(" · ") || "—"],
  ]), el("h3", t("history")));
  if (row.price_history.length) content.append(table([t("month"), t("price"), t("priceBasis")],
    row.price_history.map((v) => [day(v.observed_at), formatPrice(v), t("basis_" + v.price_basis)])));
  else content.append(el("p", t("noHistory"), "muted"));
  if (Object.keys(row.nearby).length) {
    content.append(el("h3", t("nearby")), el("p", t("straight"), "muted"),
      table([t("kind"), t("area"), t("km")], Object.entries(row.nearby).map(([key, point]) => [
        t("point_" + key), point.name, fmt(point.distance_km),
      ])));
  }
  if (row.url) content.append(link(row.url, t("original")));
  popup(listingTitle(row), content);
}

function comparison() {
  const items = state.data.listings.filter((row) => state.compare.has(row.listing_id));
  popup(t("compare"), table([t("indicator"), ...items.map(listingTitle)], [
    [t("area"), ...items.map(locationLabel)], [t("price"), ...items.map(formatPrice)],
    [t("land"), ...items.map((r) => fmt(r.land_m2))], [t("built"), ...items.map((r) => fmt(r.built_m2))],
    [t("availability"), ...items.map((r) => t("status_" + r.availability))],
    [t("verifiedAt"), ...items.map((r) => day(r.last_verified))],
    [t("source"), ...items.map((r) => link(r.url, t("original")))],
  ]));
}

let map, mapMarkers;
function renderMap(rows) {
  $("mapHint").textContent = t(rows.some((row) => row.latitude !== null) ? "straight" : "mapNoPins");
  if (!window.L) { $("map").textContent = t("mapFail"); return; }
  if (!map) {
    map = L.map("map", {scrollWheelZoom: false, maxBounds: [[14, 48], [30, 64]]}).setView([21.5, 57.1], 6);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>',
    }).addTo(map);
    mapMarkers = L.layerGroup().addTo(map);
  }
  map.invalidateSize();
  mapMarkers.clearLayers();
  $("layers").replaceChildren();
  for (const key of LAYERS) {
    const label = el("label");
    const check = el("input");
    check.type = "checkbox";
    check.checked = state.layers.has(key);
    check.addEventListener("change", () => {
      if (check.checked) state.layers.add(key);
      else state.layers.delete(key);
      renderMap(rows);
      $("layers").querySelectorAll("input")[LAYERS.indexOf(key)]?.focus();
    });
    label.append(check, el("span", t(key === "propertiesLayer" ? key : "point_" + key)));
    $("layers").append(label);
  }
  for (const row of rows) {
    if (!state.layers.has("propertiesLayer") || row.latitude === null) continue;
    const card = el("div");
    card.dir = state.lang === "ar" ? "rtl" : "ltr";
    card.append(el("strong", listingTitle(row)), el("p", formatPrice(row)), button(t("details"), () => details(row)));
    L.circleMarker([row.latitude, row.longitude], {radius: 8, color: "#005a4f", fillOpacity: .65}).bindPopup(card).addTo(mapMarkers);
  }
  for (const point of state.data.points) {
    if (!state.layers.has(point.category)) continue;
    const title = point.name || t("point_" + point.category);
    L.circleMarker([point.latitude, point.longitude], {radius: 5, color: "#124b84", fillOpacity: .72})
      .bindTooltip(el("span", title)).addTo(mapMarkers);
  }
}

function renderDirectory() {
  const rows = state.data.listings.filter((row) => matches(row, state.filters));
  const order = state.filters.sort;
  rows.sort((a, b) => {
    if (order === "lowest" || order === "highest") {
      const first = a.currency === "OMR" && a.price !== null;
      const second = b.currency === "OMR" && b.price !== null;
      if (first !== second) return first ? -1 : 1;
      if (first && second) return order === "lowest" ? Number(a.price) - Number(b.price) : Number(b.price) - Number(a.price);
    }
    return (b.last_observed ?? "").localeCompare(a.last_observed ?? "");
  });
  $("count").textContent = fmt(rows.length, 0) + " " + t("results");
  $("compare").hidden = state.compare.size === 0;
  $("compare").textContent = t("compare") + " (" + fmt(state.compare.size, 0) + ")";
  $("views").querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.view === state.view)));
  $("mapPane").hidden = state.view !== "map";
  $("listings").hidden = state.view === "map";
  if (state.view === "map") { renderMap(rows); return; }
  if (!rows.length) {
    $("listings").className = "";
    $("listings").replaceChildren(state.data.listings.length ? empty("noMatches", "adjust") : empty("noListings", "noListingsText", true));
    return;
  }
  $("listings").className = state.view === "list" ? "results-list" : "results-grid";
  $("listings").replaceChildren(...rows.map(listingCard));
}

const grouped = (items, getKey) => {
  const result = new Map();
  for (const item of items) {
    const key = getKey(item);
    if (!result.has(key)) result.set(key, []);
    result.get(key).push(item);
  }
  return result;
};
const quantile = (sorted, fraction) => {
  if (!sorted.length) return null;
  const position = (sorted.length - 1) * fraction;
  const lower = Math.floor(position);
  return sorted[lower] + (sorted[Math.ceil(position)] - sorted[lower]) * (position - lower);
};
const numberList = (values) => values.filter((value) => value !== null && value !== undefined).map(Number).sort((a, b) => a - b);
const median = (values) => quantile(numberList(values), .5);
const marketHasMonth = (month) => !month ? !(state.market.periodFrom || state.market.periodTo) :
  (!state.market.periodFrom || month >= state.market.periodFrom) && (!state.market.periodTo || month <= state.market.periodTo);

function metric(label, value) {
  const box = el("article", null, "metric");
  box.append(el("span", t(label), "muted"), el("strong", value));
  return box;
}

function marketPanel(title, content) {
  const box = el("section", null, "panel");
  box.append(el("h2", t(title)), content);
  return box;
}

function describeGroup([source, kind, deal, currency, period]) {
  return [state.data.sources[source]?.name, t("kind_" + kind), t("deal_" + deal), currency,
    period && t("period_" + period)].filter(Boolean).join(" · ");
}

function priceGroup(row, observation = row) {
  const {price, currency, price_basis, deal, rental_period, kind} = observation;
  return price !== null && currency && kind && deal && price_basis === "advertised" && (deal !== "rent" || rental_period) ?
    [row.source_id, kind, deal, currency, rental_period] : null;
}

function renderMarket() {
  const rows = state.data.listings.filter((row) => matches(row, state.market));
  const subset = rows.map((row) => ({
    row, observations: row.observations.filter((o) => marketHasMonth(o.observed_at?.slice(0, 7))),
    history: row.price_history.filter((o) => o.previous !== null && marketHasMonth(o.observed_at?.slice(0, 7))),
  })).filter((r) => r.observations.length || !(state.market.periodFrom || state.market.periodTo));
  const included = subset.map(({row}) => row);
  const unique = new Set(included.map((row) => row.canonical_group ? "p" + row.canonical_group : "l" + row.listing_id)).size;
  const known = ["governorate", "wilayat", "kind", "deal", "price", "currency"];
  const due = included.reduce((sum, row) => sum + known.filter((key) => row[key] != null).length, 0);
  const duration = subset.filter(({observations}) => observations.length >= 2).map(({observations}) =>
    (Date.parse(observations.at(-1).observed_at) - Date.parse(observations[0].observed_at)) / 86400000);
  const obs = subset.reduce((sum, item) => sum + item.observations.length, 0);
  $("summary").replaceChildren(metric("observations", fmt(obs, 0)), metric("distinct", fmt(included.length, 0)),
    metric("unique", included.length ? fmt(unique, 0) : "—"), metric("duplicateRate",
      included.length ? fmt(100 * included.filter((row) => row.duplicate_candidates).length / included.length) + "%" : "—"),
    metric("complete", included.length ? fmt(100 * due / (included.length * known.length)) + "%" : "—"), metric("duration", fmt(median(duration))));
  const marketData = $("marketData");
  marketData.replaceChildren();
  if (!included.length) {
    marketData.append(el("p", t("marketEmpty"), "muted"));
  } else {
    marketData.append(el("p", t("estimateNote"), "muted"));
    const distribution = [];
    const groups = [
      [t("gov"), "governorate", (v) => governorOptions().find(([id]) => id === v)?.[1]],
      [t("wilaya"), "wilayat", (v) => locationOptions().find(([id]) => id === v)?.[1]],
      [t("kind"), "kind", (v) => t("kind_" + v)], [t("availability"), "availability", (v) => t("status_" + v)],
      [t("source"), "source_id", (v) => state.data.sources[v]?.name],
      [t("quality"), "quality_flags", (v) => t(v ? "flagged" : "clear")],
    ];
    for (const [domain, key, translate] of groups) {
      for (const [value, items] of grouped(included, (r) => key === "quality_flags" ? Boolean(r[key].length) :
        key === "availability" ? subset.find((item) => item.row === r)?.observations.at(-1)?.availability ?? r[key] : r[key])) {
        distribution.push([domain, value != null ? translate(value) : "—", fmt(items.length, 0)]);
      }
    }
    const byLatest = [];
    const byMonth = [];
    const first = [];
    const changes = [];
    for (const item of subset) {
      const {row, observations, history} = item;
      const latest = observations.at(-1) ?? row;
      const group = priceGroup(row, latest);
      if (group) byLatest.push({group, price: latest.price, sqm: latest.price_per_m2});
      const latestByMonth = grouped(observations, (o) => o.observed_at.slice(0, 7));
      for (const [month, readings] of latestByMonth) {
        const reading = readings.at(-1);
        const key = priceGroup(row, reading);
        if (key) byMonth.push({month, group: key, price: reading.price, sqm: reading.price_per_m2});
      }
      if (row.first_observed && marketHasMonth(row.first_observed.slice(0, 7))) first.push(row.first_observed.slice(0, 7));
      for (const change of history) if (change.price_basis === "advertised") changes.push(change.observed_at.slice(0, 7));
    }
    const distributions = [...grouped(byLatest, (v) => JSON.stringify(v.group)).values()].map((items) => {
      const values = numberList(items.map((v) => v.price));
      return [describeGroup(items[0].group), fmt(items.length, 0), fmt(values[0]), fmt(quantile(values, .5)),
        fmt(values.at(-1)), fmt(median(items.map((v) => v.sqm)))];
    });
    const history = [...grouped(byMonth, (v) => JSON.stringify([v.month, v.group])).values()]
      .sort((a, b) => b[0].month.localeCompare(a[0].month)).map((items) => [
        items[0].month, describeGroup(items[0].group), fmt(items.length, 0), fmt(median(items.map((v) => v.price))),
        fmt(median(items.map((v) => v.sqm))),
      ]);
    const months = [...new Set([...first, ...changes])].sort().reverse();
    const activity = months.map((month) => [month, fmt(first.filter((x) => x === month).length, 0), fmt(changes.filter((x) => x === month).length, 0)]);
    const panels = el("div", null, "market-grid");
    const headers = (keys) => keys.map(t);
    panels.append(marketPanel("distribution", table(headers(["kind", "indicator", "n"]), distribution)),
      marketPanel("currentPrices", table(headers(["kind", "n", "min", "median", "max", "sqm"]), distributions)),
      marketPanel("newListings", table(headers(["month", "n", "changes"]), activity)),
      marketPanel("priceTrends", table(headers(["month", "kind", "n", "median", "sqm"]), history)));
    marketData.append(panels);
  }
  renderOfficial();
}

function renderOfficial() {
  const rerender = () => renderOfficial();
  const stats = state.data.official_statistics;
  const sourceNames = Object.entries(state.data.sources).filter(([key]) => stats.some((r) => r.source_id === key));
  const sources = sourceNames.map(([key, source]) => [key, sourceName(key, source)]);
  const labels = localizedPairs(STAT_INDICATORS, "stat_");
  const select = (key, options) => field(key, state.official, rerender, "select", options);
  $("officialControls").replaceChildren(select("officialSource", sources), select("chartMetric", labels));
  const region = state.market.wilaya || state.market.gov || "oman";
  const selected = stats.filter((row) => row.geography === region && marketHasMonth(row.period) &&
    (!state.official.officialSource || row.source_id === state.official.officialSource) &&
    (!state.official.chartMetric || row.indicator === state.official.chartMetric))
    .sort((a, b) => b.period.localeCompare(a.period) || a.indicator.localeCompare(b.indicator));
  const target = $("officialData");
  if (!selected.length) {
    target.replaceChildren(el("p", t("noOfficial"), "muted"));
    return;
  }
  const chartMetric = state.official.chartMetric || (selected.some((row) => row.indicator === STAT_INDICATORS[0]) ?
    STAT_INDICATORS[0] : selected[0].indicator);
  const chartRecords = selected.filter((row) => row.indicator === chartMetric).slice(0, 12).reverse();
  const max = Math.max(1, ...chartRecords.map((row) => Number(row.value)));
  const chart = el("div", null, "chart");
  chart.append(el("h3", t("stat_" + chartMetric)));
  for (const row of chartRecords) {
    const bar = el("div", null, "bar-row");
    const meter = el("meter");
    meter.max = max;
    meter.value = Number(row.value);
    meter.setAttribute("aria-label", t("stat_" + chartMetric) + " " + row.period);
    bar.append(el("span", row.period), meter, el("strong", fmt(Number(row.value)) + " " + t("unit_" + row.unit)));
    chart.append(bar);
  }
  target.replaceChildren(chart, table([t("month"), t("indicator"), t("value"), t("source")], selected.map((row) => [
    row.period, t("stat_" + row.indicator), fmt(Number(row.value)) + " " + t("unit_" + row.unit),
    link(row.url, sourceName(row.source_id, state.data.sources[row.source_id])),
  ])));
}

function sourceName(key, source) {
  if (state.lang === "ar" && key === "ncsi") return "المركز الوطني للإحصاء والمعلومات";
  if (state.lang === "ar" && key === "mohup") return "وزارة الإسكان والتخطيط العمراني";
  return source?.name ?? key;
}

function renderSources() {
  $("sourceList").replaceChildren();
  for (const [key, source] of Object.entries(state.data.sources)) {
    const card = el("article", null, "panel");
    card.append(el("h2", sourceName(key, source)));
    if (key === "osm") {
      card.append(el("p", state.lang === "ar" ? "الخريطة تغطي السلطنة. الخدمات المتاحة في هذه النسخة تغطي جزءاً من مسقط." : source.coverage, "muted"),
        el("p", "© OpenStreetMap contributors · ODbL", "muted"));
    } else card.append(el("p", t("allG") + " · " + t("country"), "muted"));
    const actions = el("div", null, "actions");
    actions.append(link(source.url, t("original")));
    if (source.terms) actions.append(link(source.terms, t("license")));
    if (key === "osm") actions.append(link("https://www.openstreetmap.org/fixthemap", t("mapIssue")));
    card.append(actions);
    $("sourceList").append(card);
  }
}

function showPage() {
  const hash = location.hash.slice(1);
  const page = MAIN_VIEWS.includes(hash) ? hash : "directory";
  $("pageTitle").textContent = t(page + "Title");
  $("pageLead").textContent = t(page + "Lead");
  document.querySelectorAll("nav a").forEach((anchor) => {
    if (anchor.getAttribute("href") === "#" + page) anchor.setAttribute("aria-current", "page");
    else anchor.removeAttribute("aria-current");
  });
  if (!state.data) return;
  MAIN_VIEWS.forEach((view) => { $(view).hidden = page !== view; });
  if (page === "directory") renderDirectory();
  if (page === "market") renderMarket();
  if (page === "sources") renderSources();
}

function localize() {
  document.documentElement.lang = state.lang;
  document.documentElement.dir = state.lang === "ar" ? "rtl" : "ltr";
  document.title = t("brand");
  $("language").textContent = state.lang === "ar" ? "English" : "العربية";
  $("language").lang = state.lang === "ar" ? "en" : "ar";
  document.querySelectorAll("[data-t]").forEach((node) => { node.textContent = t(node.dataset.t); });
  $("loadStatus").textContent = t(state.error ? "fail" : "loading");
  if (state.data) {
    $("heroNumber").textContent = fmt(state.data.geography.governorates.length, 0);
    $("updated").textContent = t("updated") + " · " + day(state.data.built_at);
    makeFilters();
  }
  showPage();
}

$("language").addEventListener("click", () => {
  state.lang = state.lang === "ar" ? "en" : "ar";
  localize();
});
$("filters").addEventListener("submit", (event) => event.preventDefault());
$("filters").addEventListener("reset", (event) => {
  event.preventDefault();
  state.filters = {};
  makeFilters();
  renderDirectory();
});
$("sort").addEventListener("change", () => { state.filters.sort = $("sort").value; renderDirectory(); });
$("views").addEventListener("click", (event) => {
  if (!event.target.dataset.view) return;
  state.view = event.target.dataset.view;
  renderDirectory();
});
$("compare").addEventListener("click", comparison);
$("closeDialog").addEventListener("click", () => $("dialog").close());
window.addEventListener("hashchange", showPage);
localize();
fetch("public-data.json")
  .then((response) => { if (!response.ok) throw new Error("Data unavailable"); return response.json(); })
  .then((payload) => {
    if (payload.schema_version !== 1) throw new Error("Unsupported data version");
    state.data = payload;
    $("loadStatus").hidden = true;
    localize();
  })
  .catch(() => { state.error = true; localize(); });
