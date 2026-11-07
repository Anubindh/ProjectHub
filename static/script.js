
function filterItems(searchId, statusId, itemClass) {

    const searchValue = document
        .getElementById(searchId)
        .value.toLowerCase();

    const statusValue = document
        .getElementById(statusId)
        .value.toLowerCase();

    const items = document.querySelectorAll('.' + itemClass);

    items.forEach(item => {

        const text = item.innerText.toLowerCase();

        const matchesSearch = text.includes(searchValue);
        const matchesStatus = !statusValue ||
            text.includes(statusValue);

        item.style.display =
            matchesSearch && matchesStatus ? '' : 'none';

    });
}
