# Changelog

## Current (in progress)

- Nothing yet

## 4.0.0 (2024-01-09)

- :warning: Add migration from ODS to DCAT [#247](https://github.com/opendatateam/udata-ods/pull/247)
    - All ODS harvest sources are converted to DCAT
    - Datasets are updated with new remote_id and new resources urls
- Add migration that removes duplicate resources [#248](https://github.com/opendatateam/udata-ods/pull/248)

## 3.0.1 (2023-02-06)

- Fix can_explore on dataset with both ODS and non-ODS resources [#244](https://github.com/opendatateam/udata-ods/pull/244)

## 3.0.0 (2022-11-14)

- :warning: **Breaking change** Use harvest dynamic field introduced in udata 5 [#234](https://github.com/opendatateam/udata-ods/pull/234)
- Store geojson format instead of json when relevant [#212](https://github.com/opendatateam/udata-ods/pull/212)
- Replace mongo legacy image in CI [#221](https://github.com/opendatateam/udata-ods/pull/221)

## 2.1.0 (2020-10-16)

- Link exports (resources) to a version of the file with machine names as headers, instead of labels [#169](https://github.com/opendatateam/udata-ods/pull/169)

## 2.0.1 (2020-03-24)

- Use `metas[modified]` -> `dataset.last_modified` [#148](https://github.com/opendatateam/udata-ods/pull/148)

## 2.0.0 (2020-03-11)

- Migrate to python3 🐍 [#91](https://github.com/opendatateam/udata-ods/pull/91)

## 1.2.4 (2019-05-29)

- Fill extras.remote_url [#111](https://github.com/opendatateam/udata-ods/pull/111)

## 1.2.3 (2019-03-27)

- Fetch each dataset metadata on processing instead of once on initialization (ensures fresher metadata) [#98](https://github.com/opendatateam/udata-ods/pull/98)

## 1.2.2 (2019-02-01)

- Ensure dataset with only attachments or alternative exports are properly harvested [#86](https://github.com/opendatateam/udata-ods/pull/86)

## 1.2.1 (2018-10-02)

- Fix dependency on udata 1.6.0 (instead of 1.6.0.dev)

## 1.2.0 (2018-10-02)

- Initial filtering support [#52](https://github.com/opendatateam/udata-ods/pull/52)  [#61](https://github.com/opendatateam/udata-ods/pull/61)
- Optionnal Inspire dataset harvesting [#61](https://github.com/opendatateam/udata-ods/pull/61)
- Fix missing translations [#53](https://github.com/opendatateam/udata-ods/pull/53)

## 1.1.0 (2018-06-06)

- Initial i18n support [#20](https://github.com/opendatateam/udata-ods/pull/20)
- Do not export SHP when above records limit [#26](https://github.com/opendatateam/udata-ods/pull/20)
- Initial resources preview support [#29](https://github.com/opendatateam/udata-ods/pull/29) [#34](https://github.com/opendatateam/udata-ods/pull/34)
- Use `udata.frontend.markdown:parse_html()` to parse description [#35](https://github.com/opendatateam/udata-ods/pull/35)
- Attachments support [#36](https://github.com/opendatateam/udata-ods/pull/36)
- Register `ods:` prefixed extras [#42](https://github.com/opendatateam/udata-ods/pull/42)

## 1.0.1 (2018-03-13)

- Fix URLs handling (no double slashes) [#2](https://github.com/opendatateam/udata-ods/pull/2)
- Fix packaging [#3](https://github.com/opendatateam/udata-ods/pull/3)
- Make use of [udata pytest plugin](opendatateam/udata#1400) [#4](https://github.com/opendatateam/udata-ods/pull/4)
- Alternative exports support [#14](https://github.com/opendatateam/udata-ods/pull/14)

## 1.0.0 (2017-10-20)

- Initial release
