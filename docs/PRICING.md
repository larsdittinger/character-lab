# GPT Image 2.5 settings and pricing

The generator defaults to **`gpt-image-2.5-sunburst`**, **`quality=high`**, **`size=1536x1024`**, **`n=1`**, PNG and an opaque background. Sunburst prioritizes quality; Flare is the optional faster variant (`--model gpt-image-2.5-flare`). The image API uses `quality`, not `reasoning_effort`. [Official Sunburst documentation](https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst), [image generation parameters](https://developers.openai.com/api/docs/guides/image-generation).

Verified September 25, 2026: both models charge $5 per million text input tokens, $8 per million image input tokens and $30 per million image output tokens, with lower rates for cached input. Equal rates do not imply equal token counts or image costs. [Official pricing](https://developers.openai.com/api/docs/pricing).

“A few Czech crowns per model” is not a guaranteed price. The API creates a reference; mesh construction and animation run locally. A three-view sheet is one image. Reference cost depends on actual `usage`, dimensions, quality and any input images; conversion to CZK also depends on the payment provider's exchange rate. The helper records usage and `actualBilledUsd: null` because it does not read an invoice.

During this integration, a read-only model-list request confirmed account access to Sunburst and Flare. No new paid reference image was generated. Generation and edit request handling are tested offline; a future sheet still needs visual inspection after an actual request.

Set `OPENAI_API_KEY` in the environment or this directory's ignored `.env`. The helper never automatically repeats paid requests. A failed attempt leaves a `.pending` record; investigate its request status before retrying with another name. Do not blindly remove that record after a timeout and charge for the same request again.

The knight retains its historical Gemini references. Ranger and elf retain their built-in ImageGen references. Switching the future helper does not change the provenance of those images or add generation costs to offline rebuilds.
