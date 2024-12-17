import { Client } from "@opensearch-project/opensearch";

const esClient = new Client({
    node: "https://search-photos-search-a3enfdo3dugpg5ba6msyyctykm.us-east-1.es.amazonaws.com", // Replace with your OpenSearch endpoint
    auth: {
        username: "Stuti", // Replace with your OpenSearch username
        password: "Bingo@1234"  // Replace with your OpenSearch password
    }
});

export const handler = async (event) => {
    try {
        console.log("Lex Event:", JSON.stringify(event, null, 2));

        // Extract slots from the Lex event
        const keyword1 = event.keyword1
        const keyword2 = event.keyword2

        // Ensure at least one keyword is provided
        if (!keyword1) {
            return {
                statusCode:404,
                data: [
                    { contentType: "PlainText", content: "Please provide at least one keyword to search." }
                ]
            };
        }

        // Build OpenSearch query
        const keywords = [keyword1];
        if (keyword2) {
            keywords.push(keyword2);
        }

        const query = {
            query: {
                terms: {
                    labels: keywords
                }
            }
        };

        // Execute OpenSearch query
        const searchParams = {
            index: "photos", // Replace with your OpenSearch index
            body: query
        };

        const searchResult = await esClient.search(searchParams);
        console.log("Search results:", JSON.stringify(searchResult.body, null, 2));

        // Extract results
        const hits = searchResult.body.hits.hits || [];
        if (hits.length === 0) {
            return {
                statusCode:200,
                data: [
                    { contentType: "PlainText", content: `No results found for keywords: ${keywords.join(", ")}` }
                ]
            };
        }

        // Prepare response cards
        const responseCards = hits.map((hit) => {
            const { s3_key, s3_bucket, labels } = hit._source;
            return {
                title: s3_bucket,
                imageUrl: `https://${s3_bucket}.s3.amazonaws.com/${s3_key}`,
                subtitle: `Labels: ${labels.join(", ")}`
            };
        });

        return {
            statusCode:200,
            data: [
                {
                    contentType: "CustomPayload",
                    content: JSON.stringify(responseCards)
                }
            ]
        };
    } catch (error) {
        console.error("Error in Lambda:", error);
        return {
            statusCode:500,
            data: [
                { contentType: "PlainText", content: "An error occurred while processing your request." }
            ]
        };
    }
};
