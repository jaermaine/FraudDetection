import { predictFraud } from './fraudDetection.js';

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('transactionForm');
    const resultsContainer = document.getElementById('analysisResults');

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            // Get form data
            const formData = {
                amount: parseFloat(form.amount.value),
                type: form.transactionType.value,
                oldbalanceOrg: parseFloat(form.oldbalanceOrg.value),
                newbalanceOrig: parseFloat(form.newbalanceOrig.value),
                oldbalanceDest: parseFloat(form.oldbalanceDest.value),
                newbalanceDest: parseFloat(form.newbalanceDest.value)
            };

            // Analyze transaction
            const analysis = await predictFraud(formData);

            // Display results
            if (resultsContainer) {
                resultsContainer.classList.remove('hidden');
                
                if (analysis.error) {
                    // Display error state
                    resultsContainer.className = 'analysis-results result-error';
                    resultsContainer.innerHTML = `
                        <div class="result-header">
                            <h2>Analysis Error</h2>
                            <span class="status-badge error">Error</span>
                        </div>
                        <p class="error-message">${analysis.message}</p>
                        <p class="error-hint">The ML model might be disconnected. Please try again later.</p>
                    `;
                } else {
                    // Display success state
                    const statusClass = analysis.is_fraud ? 'fraudulent' : 'legitimate';
                    resultsContainer.className = `analysis-results result-${statusClass}`;
                    
                    resultsContainer.innerHTML = `
                        <div class="result-header">
                            <h4>Analysis Results</h4>
                            <span class="status-badge ${statusClass}">${analysis.is_fraud ? 'FRAUDULENT' : 'LEGITIMATE'}</span>
                        </div>
                        <p class="risk-score">Fraud Probability: ${(analysis.fraud_probability * 100).toFixed(1)}%</p>
                        <p class="confidence-level">Confidence Level: <span class="confidence-${analysis.confidence.toLowerCase()}">${analysis.confidence.toUpperCase()}</span></p>
                    `;
                }
            }
        });
    }
});