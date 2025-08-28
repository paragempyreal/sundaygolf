import React, { useState } from "react";
import { configService } from "../services/configService";
import toast from "react-hot-toast";

const ProductSyncChecker: React.FC = () => {
  const [code, setCode] = useState("");
  const [mode, setMode] = useState<"live" | "test">("live");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim()) {
      toast.error("Please enter a product code");
      return;
    }
    try {
      setIsLoading(true);
      const data = await configService.checkProductSync(code.trim(), mode);
      setResult(data);
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to check product"
      );
    } finally {
      setIsLoading(false);
    }
  };

  const renderValue = (val: any) => {
    if (val === null || val === undefined)
      return <span className="text-gray-400">—</span>;
    if (typeof val === "boolean") return val ? "true" : "false";
    if (typeof val === "object")
      return (
        <pre className="text-xs bg-gray-50 p-2 rounded border overflow-x-auto">
          {JSON.stringify(val, null, 2)}
        </pre>
      );
    return String(val);
  };

  // Display fields and labels (Fulfil and ShipHero panels only)
  const displayFieldsOrder: string[] = [
    "variant_name",
    "code",
    "media",
    "upc",
    "asin",
    "buyer_sku",
    "weight",
    "length",
    "width",
    "height",
    "dimension_unit",
    "weight_uom",
    "country_of_origin",
    "hs_code",
    "quantity_per_case",
    "unit_of_measure",
  ];
  const fieldLabels: Record<string, string> = {
    variant_name: "Variant Name",
    code: "Code",
    media: "Media (Images)",
    upc: "UPC",
    asin: "ASIN",
    buyer_sku: "Buyer SKU",
    weight: "Weight",
    length: "Length",
    width: "Width",
    height: "Height",
    dimension_unit: "Dimension Unit",
    weight_uom: "Weight UOM",
    country_of_origin: "Country of Origin",
    hs_code: "HS Code",
    quantity_per_case: "Quantity per Case",
    unit_of_measure: "Unit of Measure",
  };

  // Prefer normalized payload from API; fallback to mapping raw payloads
  const chooseFulfilForCompare = (res: any) =>
    res?.normalized || res?.data || null;
  const chooseShipHeroForCompare = (res: any) =>
    res?.normalized || res?.data || null;

  // Helpers to build display models
  const safeFirst = (...vals: any[]) =>
    vals.find((v) => v !== undefined && v !== null);
  const parseMeasure = (s: any) => {
    if (typeof s !== "string") return { value: s, unit: undefined };
    const parts = s.trim().split(/\s+/);
    if (parts.length >= 2)
      return { value: parts[0], unit: parts.slice(1).join(" ") };
    return { value: s, unit: undefined };
  };

  const buildFulfilDisplay = (src: any) => {
    const codes: any[] = Array.isArray(src?.codes) ? src.codes : [];
    const findCode = (t: string) => codes.find((c) => c?.type === t)?.value;
    const upc = safeFirst(src?.upc, findCode("upc"));
    const asin = safeFirst(src?.asin, findCode("asin"));
    const buyerSku = safeFirst(src?.buyer_sku, findCode("buyer_sku"));
    const wOz = src?.weight_oz ?? src?.weight?.weight_oz;
    const wGm = src?.weight_gm ?? src?.weight?.weight_gm;
    const lenIn = safeFirst(src?.length_in, src?.dimensions?.length_in);
    const widIn = safeFirst(src?.width_in, src?.dimensions?.width_in);
    const heiIn = safeFirst(src?.height_in, src?.dimensions?.height_in);
    const lenCm = safeFirst(src?.length_cm, src?.dimensions?.length_cm);
    const widCm = safeFirst(src?.width_cm, src?.dimensions?.width_cm);
    const heiCm = safeFirst(src?.height_cm, src?.dimensions?.height_cm);
    const weight = wOz != null ? `${wOz} oz` : wGm != null ? `${wGm} gm` : null;
    const length =
      lenIn != null ? `${lenIn} in` : lenCm != null ? `${lenCm} cm` : null;
    const width =
      widIn != null ? `${widIn} in` : widCm != null ? `${widCm} cm` : null;
    const height =
      heiIn != null ? `${heiIn} in` : heiCm != null ? `${heiCm} cm` : null;
    const dimensionUnit =
      lenIn != null || widIn != null || heiIn != null
        ? "in"
        : lenCm != null || widCm != null || heiCm != null
        ? "cm"
        : null;
    const weightUom = wOz != null ? "oz" : wGm != null ? "gm" : null;
    const image = safeFirst(src?.image_url, src?.imageUrl);
    return {
      variant_name: src?.variant_name ?? src?.name,
      code: src?.code,
      media: image,
      upc,
      asin,
      buyer_sku: buyerSku,
      weight,
      length,
      width,
      height,
      dimension_unit: dimensionUnit,
      weight_uom: weightUom,
      country_of_origin:
        src?.country_of_origin ?? src?.customs_information?.country_of_origin,
      hs_code: src?.hs_code ?? src?.customs_information?.hs_code,
      quantity_per_case: src?.quantity_per_case,
      unit_of_measure: src?.unit_of_measure,
    };
  };

  const buildShipHeroDisplay = (src: any) => {
    // Accept both shapes: raw ShipHero (with dimensions) and normalized (flat fields)
    const dims = src?.dimensions || {};
    const w = parseMeasure(dims?.weight ?? src?.weight ?? src?.weight_oz);
    const l = parseMeasure(dims?.length ?? src?.length ?? src?.length_in);
    const wdt = parseMeasure(dims?.width ?? src?.width ?? src?.width_in);
    const h = parseMeasure(dims?.height ?? src?.height ?? src?.height_in);
    const mediaList: string[] = Array.isArray(src?.images)
      ? src.images
          .map((img: any) => img?.url || img?.original || img?.large || img)
          .filter(Boolean)
      : [];
    const media =
      mediaList[0] || src?.large_thumbnail || src?.thumbnail || null;
    const dimensionUnit = l.unit || wdt.unit || h.unit || null;
    const weightUom = w.unit || null;
    return {
      variant_name: src?.name,
      code: src?.sku ?? src?.code,
      media,
      upc: src?.barcode ?? src?.upc,
      asin: src?.asin ?? null,
      buyer_sku: src?.buyer_sku ?? null,
      weight:
        w.value != null ? `${w.value}${w.unit ? ` ${w.unit}` : ""}` : null,
      length:
        l.value != null ? `${l.value}${l.unit ? ` ${l.unit}` : ""}` : null,
      width:
        wdt.value != null
          ? `${wdt.value}${wdt.unit ? ` ${wdt.unit}` : ""}`
          : null,
      height:
        h.value != null ? `${h.value}${h.unit ? ` ${h.unit}` : ""}` : null,
      dimension_unit: dimensionUnit,
      weight_uom: weightUom,
      country_of_origin: src?.country_of_manufacture ?? src?.country_of_origin,
      hs_code: src?.tariff_code ?? src?.hs_code,
      quantity_per_case: src?.quantity_per_case ?? null,
      unit_of_measure: src?.unit_of_measure ?? null,
    };
  };

  const isDifferent = (a: any, b: any) => {
    const sa = a === undefined || a === null ? "" : String(a);
    const sb = b === undefined || b === null ? "" : String(b);
    return sa !== sb;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Product Sync Checker
        </h1>
        <p className="mt-2 text-sm text-gray-700">
          Verify a product across Fulfil and ShipHero. Mode-aware per
          configuration.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="bg-white shadow rounded-lg p-4 space-y-4"
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Product Code
            </label>
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              placeholder="SKU/code"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Mode
            </label>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value as "live" | "test")}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            >
              <option value="live">Live</option>
              <option value="test">Test</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              type="submit"
              disabled={isLoading}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            >
              {isLoading ? "Checking..." : "Check"}
            </button>
          </div>
        </div>
      </form>

      {result && (
        <div className="space-y-4">
          {/* Panels only: Fulfil and ShipHero */}

          {/* Side-by-side */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Fulfil */}
            <div className="bg-white shadow rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-medium text-gray-900">Fulfil</h3>
              </div>
              {result.fulfil?.error && (
                <div className="text-sm text-red-600 mb-2">
                  {result.fulfil.error}
                </div>
              )}
              {!result.fulfil?.success ? (
                <div className="text-sm text-gray-600">No product found.</div>
              ) : (
                <div className="space-y-2 text-sm">
                  {(() => {
                    const src = chooseFulfilForCompare(result.fulfil);
                    const model = buildFulfilDisplay(src);
                    return displayFieldsOrder.map((key) => (
                      <div className="grid grid-cols-3 gap-3" key={`f-${key}`}>
                        <div className="text-gray-500">{fieldLabels[key]}</div>
                        <div className="col-span-2 font-mono">
                          {renderValue((model as any)[key])}
                        </div>
                      </div>
                    ));
                  })()}
                </div>
              )}
            </div>

            {/* ShipHero */}
            <div className="bg-white shadow rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-medium text-gray-900">ShipHero</h3>
              </div>
              {result.shiphero?.error && (
                <div className="text-sm text-red-600 mb-2">
                  {result.shiphero.error}
                </div>
              )}
              {!result.shiphero?.success ? (
                <div className="text-sm text-gray-600">No product found.</div>
              ) : (
                <div className="space-y-2 text-sm">
                  {(() => {
                    const src = chooseShipHeroForCompare(result.shiphero);
                    const model = buildShipHeroDisplay(src);
                    return displayFieldsOrder.map((key) => (
                      <div className="grid grid-cols-3 gap-3" key={`s-${key}`}>
                        <div className="text-gray-500">{fieldLabels[key]}</div>
                        <div className="col-span-2 font-mono">
                          {renderValue((model as any)[key])}
                        </div>
                      </div>
                    ));
                  })()}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductSyncChecker;
