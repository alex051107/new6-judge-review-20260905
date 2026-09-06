# Build the parcel-rate workpaper
Build `/app/output/answer.xlsx` from the supplied USPS Notice 123 and quote requests. Extract the July 12, 2026 retail Priority Mail and USPS Ground Advantage rate grids for zones 1–8 and the weight range defined in `review_brief.md`, preserving service, weight-band, unit and page identity.

For each request, show the applicable rate for both services and the lower-price option, and provide a batch total. Use only the supported ordinary-parcel conditions in the brief; this is a price comparison, not a delivery-time recommendation.

The rate extraction must be reviewable. Quote results and totals must update when an in-scope request's weight or zone changes. Preserve the original rate facts and request IDs, and explain any out-of-scope input rather than silently using another product or pricing schedule.
