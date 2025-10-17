(() => {
    const articleTitle = document.title || 'No title found';

    // Find the first paragraph with a decent amount of text
    const firstParagraph = document.querySelector('p')?.innerText || 'No paragraph found';

    return { title: articleTitle, paragraph: firstParagraph };
})();