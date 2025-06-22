import stashapi.log as log
from stashapi.stashapp import StashInterface
import sys
import json


def processAll():
    pass


def processImage(imageId):
    image = stash.find_image(imageId)
    if image is None:
        log.error(f"Image with id {imageId} not found")
        return

    if settings["demandOrganized"] and not image["organized"]:
        log.info(f"Excluding image {imageId} because it is not organized")
        return
    
    imageTagIds = [tag["id"] for tag in image["tags"]]
    if settings["excludeImageWithTag"] != "":
        imageExclusionMarkerTag = stash.find_tag(settings["excludeImageWithTag"])
        if imageExclusionMarkerTag is not None:
            if imageExclusionMarkerTag["id"] in imageTagIds:
                log.info(f"Excluding image {imageId} because it has the tag {settings['excludeImageWithTag']}")
                return
            
    galleryQuery = {
        "images_filter": {
            "id": {
                "value": imageId,
                "modifier": "EQUALS"
            }
        }
    }
    if settings['excludeOrganized']:
        galleryQuery["organized"] = False # type: ignore
    
    if settings["excludeGalleryWithTag"] != "":
        galleryExclusionMarkerTag = stash.find_tag(settings["excludeGalleryWithTag"])
        if galleryExclusionMarkerTag is not None:
            imageTagIds.append(galleryExclusionMarkerTag["id"])

    galleryCount = stash.find_galleries(f=galleryQuery, filter={"page": 0, "per_page": 0}, get_count=True)[0]

    if galleryCount > 0:
        performerIds = [performer["id"] for performer in image["performers"]]

        log.info(f"Updating {galleryCount} galleries of image \"{image['title']}\" with tags {image['tags']}")

        galleryPageSize = 100
        galleryPage = 0
        while galleryPage * galleryPageSize < galleryCount:
            galleries = stash.find_galleries(f=galleryQuery, filter={"page": galleryPage, "per_page": galleryPageSize}, fragment='id')
            galleryIds = [gallery['id'] for gallery in galleries]

            stash.update_galleries(
                {
                    "ids": galleryIds,
                    "performer_ids": {"mode": "ADD", "ids": performerIds},
                    "tag_ids": {"mode": "ADD", "ids": imageTagIds}
                }
            )
            log.debug(f"Updated {len(galleryIds)} galleries of image {imageId}")
            galleryPage += 1
    


json_input = json.loads(sys.stdin.read())
FRAGMENT_SERVER = json_input["server_connection"]
stash = StashInterface(FRAGMENT_SERVER)
config = stash.get_configuration()
settings = {
    "excludeOrganized": False,
    "demandOrganized": True,
    "excludeImageWithTag": "",
    "excludeGalleryWithTag": "",
}
if "tagGalleriesWithImageTags" in config["plugins"]:
    settings.update(config["plugins"]["tagGalleriesWithImageTags"])
if "hookContext" in json_input["args"]:
    id = json_input["args"]["hookContext"]["id"]
    if json_input["args"]["hookContext"]["type"] in {"Image.Update.Post", "Image.Create.Post"}:
        log.info(f"Processing Image {id}")
        processImage(id)
