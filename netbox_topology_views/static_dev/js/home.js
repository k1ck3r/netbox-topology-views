let container = null
let downloadButton = null
const MIME_TYPE = 'image/png'
let canvas = null
let csrftoken = null
const options = {
    interaction: {
        hover: true,
        hoverConnectedEdges: true,
        multiselect: false
    },
    nodes: {
        shape: 'image',
        brokenImage: '../../static/netbox_topology_views/img/role-unknown.png',
        size: 35,
        font: {
            multi: 'md',
            face: 'helvetica'
        }
    },
    edges: {
        length: 100,
        width: 2,
        font: {
            face: 'helvetica'
        }
    },
    physics: {
        solver: 'forceAtlas2Based'
    }
}
let coordSaveCheckbox = null
let htmlElement = null

const getCookie = (name) => {
    if (!document.cookie) return null

    const cookie = document.cookie
        .split(';')
        .find((cookie) => {
            return cookie.trim().substring(0, name.length + 1) === name + '='
        })
        ?.substring(name.length + 1)

    return cookie ? decodeURIComponent(cookie) : null
}

const htmlTitle = (html) => {
    const container = document.createElement('div')
    container.innerHTML = html
    return container
}

const handleLoadData = async (power = false) => {
    const query = new URLSearchParams(location.toString())

    if (power) query.append('power_only', 'true')
    const panel = document.querySelector('.panel-body')

    panel.classList.add('loading')

    const res = await fetch(
        `/api/plugins/netbox_topology_views/topology/?${query}`
    )

    const topologyData = await res.json()

    if (topologyData === null) return
    if (htmlElement.dataset.netboxColorMode == 'dark') {
        options.nodes.font.color = '#fff'
    }

    const nodes = new vis.DataSet()
    const edges = new vis.DataSet()
    const graph = new vis.Network(container, { nodes, edges }, options)

    topologyData.edges.forEach((edge) => {
        edge.title = htmlTitle(edge.title)
        edges.add(edge)
    })

    topologyData.nodes.forEach((node) => {
        node.title = htmlTitle(node.title)
        nodes.add(node)
    })

    graph.fit()
    panel.classList.remove('loading')

    canvas = document
        .getElementById('visgraph')
        .getElementsByTagName('canvas')[0]

    graph.on('afterDrawing', () => {
        const image = canvas.toDataURL(MIME_TYPE)
        downloadButton.href = image
        downloadButton.download = 'topology'
    })

    graph.on(
        'click',
        (params) =>
            params.nodes.length === 1 &&
            window.open(nodes.get(params.nodes[0]).href, '_blank')
    )

    graph.on('dragEnd', (params) => {
        if (!coordSaveCheckbox.checked) return
        this.getPositions(params.nodes).forEach(async (node) => {
            const res = await fetch(
                '/api/plugins/netbox_topology_views/save-coords/',
                {
                    method: 'PATH',
                    headers: {
                        'X-CSRFToken': csrftoken,
                        Accept: 'application/json',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        node_id: node,
                        x: dragged[node].x,
                        y: dragged[node].y
                    })
                }
            )

            console.log(node, res.status, res.statusText)
        })
    })
}

document.querySelector('#network-tab').addEventListener('click', async () => {
    await handleLoadData(false)
})
document.querySelector('#power-tab').addEventListener('click', async () => {
    await handleLoadData(true)
})

document.addEventListener(
    'DOMContentLoaded',
    async () => {
        csrftoken = getCookie('csrftoken')
        container = document.getElementById('visgraph')
        htmlElement = document.getElementsByTagName('html')[0]
        await handleLoadData()
        downloadButton = document.getElementById('btnDownloadImage')
        btnFullView = document.getElementById('btnFullView')
        coordSaveCheckbox = document.getElementById('id_save_coords')
    },
    false
)
