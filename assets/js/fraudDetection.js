export async function predictFraud(transactionData) {
    try {
        const response = await fetch('http://localhost:8000/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                type: transactionData.type,
                amount: parseFloat(transactionData.amount),
                oldbalanceOrg: parseFloat(transactionData.oldbalanceOrg),
                newbalanceOrig: parseFloat(transactionData.newbalanceOrig),
                oldbalanceDest: parseFloat(transactionData.oldbalanceDest),
                newbalanceDest: parseFloat(transactionData.newbalanceDest)
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            let errorMessage = 'Error making prediction';
            try {
                const errorJson = JSON.parse(errorText);
                errorMessage = errorJson.detail || errorMessage;
            } catch (e) {
                errorMessage = errorText || errorMessage;
            }
            throw new Error(errorMessage);
        }

        const result = await response.json();
        
        if (result.is_fraud) {
            console.log(`⚠️ FRAUD DETECTED!`);
            console.log(`Probability: ${(result.fraud_probability * 100).toFixed(2)}%`);
            console.log(`Confidence: ${result.confidence}`);
        } else {
            console.log(`✅ Transaction appears legitimate`);
            console.log(`Fraud Probability: ${(result.fraud_probability * 100).toFixed(2)}%`);
        }
        
        return result;
    } catch (error) {
        console.error('Error:', error);
        return {
            error: true,
            message: error.message || 'Network error or server is not responding'
        };
    }
}