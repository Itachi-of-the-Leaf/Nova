import puppeteer from 'puppeteer';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

(async () => {
    const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
    const page = await browser.newPage();

    try {
        console.log("Navigating to frontend...");
        await page.goto('http://localhost:3000', { waitUntil: 'networkidle0' });

        console.log("Uploading file...");
        const fileInput = await page.$('input[type="file"]');
        const filePath = path.resolve(__dirname, '../backend/data/temp.docx');
        await fileInput.uploadFile(filePath);

        console.log("Waiting for verification step (This may take up to 2-3 minutes due to LLM)...");
        await page.waitForSelector('.bg-white.rounded-2xl.border', { timeout: 180000 });

        const confidenceScore = await page.evaluate(() => {
            const h3s = Array.from(document.querySelectorAll('h3'));
            const h3 = h3s.find(el => el.textContent.includes('AI Extraction Confidence'));
            return h3 && h3.nextElementSibling ? h3.nextElementSibling.textContent : null;
        });
        console.log('Extraction success! UI advanced to Verification Step.');
    } catch (error) {
        console.error("Test failed:", error);
        process.exit(1);
    } finally {
        await browser.close();
        process.exit(0);
    }
})();
