from pathlib import Path
import sherpa_onnx

def assert_file_exists(filename: str):
    assert Path(filename).is_file(), (
        f"{filename} does not exist!\n"
        "Please refer to "
        "https://k2-fsa.github.io/sherpa/onnx/pretrained_models/index.html to download it"
    )
def create_recognizer(args) -> sherpa_onnx.OfflineRecognizer:
    if args.encoder:
        assert len(args.paraformer) == 0, args.paraformer
        assert len(args.nemo_ctc) == 0, args.nemo_ctc
        assert len(args.whisper_encoder) == 0, args.whisper_encoder
        assert len(args.whisper_decoder) == 0, args.whisper_decoder
        assert len(args.tdnn_model) == 0, args.tdnn_model

        assert_file_exists(args.encoder)
        assert_file_exists(args.decoder)
        assert_file_exists(args.joiner)

        recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
            encoder=args.encoder,
            decoder=args.decoder,
            joiner=args.joiner,
            tokens=args.tokens,
            num_threads=args.num_threads,
            sample_rate=args.sample_rate,
            feature_dim=args.feat_dim,
            decoding_method=args.decoding_method,
            max_active_paths=args.max_active_paths,
            hotwords_file=args.hotwords_file,
            hotwords_score=args.hotwords_score,
        )
    elif args.paraformer:
        assert len(args.nemo_ctc) == 0, args.nemo_ctc
        assert len(args.whisper_encoder) == 0, args.whisper_encoder
        assert len(args.whisper_decoder) == 0, args.whisper_decoder
        assert len(args.tdnn_model) == 0, args.tdnn_model

        assert_file_exists(args.paraformer)

        recognizer = sherpa_onnx.OfflineRecognizer.from_paraformer(
            paraformer=args.paraformer,
            tokens=args.tokens,
            num_threads=args.num_threads,
            sample_rate=args.sample_rate,
            feature_dim=args.feat_dim,
            decoding_method=args.decoding_method,
        )
    elif args.nemo_ctc:
        assert len(args.whisper_encoder) == 0, args.whisper_encoder
        assert len(args.whisper_decoder) == 0, args.whisper_decoder
        assert len(args.tdnn_model) == 0, args.tdnn_model

        assert_file_exists(args.nemo_ctc)

        recognizer = sherpa_onnx.OfflineRecognizer.from_nemo_ctc(
            model=args.nemo_ctc,
            tokens=args.tokens,
            num_threads=args.num_threads,
            sample_rate=args.sample_rate,
            feature_dim=args.feat_dim,
            decoding_method=args.decoding_method,
        )
    elif args.whisper_encoder:
        assert len(args.tdnn_model) == 0, args.tdnn_model
        assert_file_exists(args.whisper_encoder)
        assert_file_exists(args.whisper_decoder)

        recognizer = sherpa_onnx.OfflineRecognizer.from_whisper(
            encoder=args.whisper_encoder,
            decoder=args.whisper_decoder,
            tokens=args.tokens,
            num_threads=args.num_threads,
            decoding_method=args.decoding_method,
            language=args.whisper_language,
            task=args.whisper_task,
        )
    elif args.tdnn_model:
        assert_file_exists(args.tdnn_model)

        recognizer = sherpa_onnx.OfflineRecognizer.from_tdnn_ctc(
            model=args.tdnn_model,
            tokens=args.tokens,
            sample_rate=args.sample_rate,
            feature_dim=args.feat_dim,
            num_threads=args.num_threads,
            decoding_method=args.decoding_method,
        )
    else:
        raise ValueError("Please specify at least one model")

    return recognizer